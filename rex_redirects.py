import click
import requests as requestslib
from pathlib import Path

from cnxcommon import ident_hash


requests = requestslib.Session()
adapter = requestslib.adapters.HTTPAdapter(max_retries=5)
requests.mount('https://', adapter)


here = Path(__file__).parent
default_openstax_host = 'openstax.org'
default_archive_host = 'archive.cnx.org'


def get_rex_release_json_url(host):
    env_url = f'https://{host}/rex/environment.json'
    release_id = requests.get(env_url).json()['release_id']
    return f'https://{host}/rex/releases/{release_id}/rex/release.json'


def get_book_slug(host, book_id):
    url = (
        f"https://{host}/apps/cms/api/v2/pages/"
        f"?type=books.Book&fields=cnx_id&format=json&cnx_id={book_id}"
    )
    book = requests.get(url).json()['items'][0]
    return book['meta']['slug']


def flatten_tree(tree):
    """Flatten a tree to a linear sequence of values."""
    yield dict([
        (k, v)
        for k, v in tree.items()
        if k != 'contents'
    ])
    if 'contents' in tree:
        for x in tree['contents']:
            for y in flatten_tree(x):
                yield y

def first_leaf(tree):
    """Find the first leaf node (Page) in the tree."""
    if 'contents' in tree:
        x = tree['contents'][0]
        return first_leaf(x)
    else:
        return tree

def rex_uri(book, page):
    if page is None:
        uri = f'/books/{book}'
    else:
        uri = f'/books/{book}/pages/{page}'
    return uri


def cnx_uri_regex(book, page):
    if page is None:
        uri_regex = f"/contents/({book['id']}|{book['short_id']})(@[.\d]+)?(/[-%\w\d]+)?$"
    else:
        uri_regex = f"/contents/({book['id']}|{book['short_id']})(@[.\d]+)?:({page['id']}|{page['short_id']})(@[.\d]+)?(/[-%\w\d]+)?$"
    return uri_regex


def expand_tree_node(node):
    result = {
        'slug': node['slug'],
        'title': node['title'],
    }
    result['id'], result['version'] = ident_hash.split_ident_hash(node['id'])
    try:
        # We raise an error for this... It maybe makes sense for the application of it in archive?
        ident_hash.split_ident_hash(node['shortId'])
    except ident_hash.IdentHashShortId as exc:
        result['short_id'] = exc.id
    return result

def get_book_tree(host, book_id):
    """Returns a list of nodes in a book's tree."""
    resp = requests.get(f'https://{host}/contents/{book_id}.json')
    metadata = resp.json()
    return metadata['tree']

def get_book_nodes(host, book_id):
    """Returns a list of nodes in a book's tree."""
    for x in flatten_tree(get_book_tree(host, book_id)):
        yield expand_tree_node(x)


def generate_nginx_uri_mappings(cnx_host, openstax_host, book):
    """\
    This creates the nginx uri map to be used inside the nginx
    configuration's `map` block.

    """
    tree = get_book_tree(cnx_host, book)
    non_preface_tree = [ x for x in tree['contents'] if 'contents' in x ][0]
    intro_page = first_leaf(non_preface_tree)

    nodes = list(get_book_nodes(cnx_host, book))
    book_node = nodes[0]
    book_slug = get_book_slug(openstax_host, book)

    uri_mappings = [
        # Book URL redirects to the first page of the REX book
        (cnx_uri_regex(book_node, None), rex_uri(book_slug, intro_page['slug']),)
    ]

    for node in nodes[1:]:  # skip the book
        uri_mappings.append(
            (cnx_uri_regex(book_node, node),
             rex_uri(book=book_slug, page=node['slug']),
            )
        )
    return uri_mappings


def write_nginx_map(uri_map, out):
    for orig_uri, dest_uri in uri_map:
        out.write(f'~{orig_uri}    {dest_uri};\n')


@click.command()
@click.option('-o', '--output', type=click.File(mode='w'))
@click.pass_context
def update_rex_redirects(ctx, output):
    release_json_url = get_rex_release_json_url(ctx.parent.params['openstax_host'])
    release_data = requests.get(release_json_url).json()
    books = [book for book in release_data['books']]
    for book in books:
        click.echo(f"Write entries for {book}.", err=True)
        book_uri_map = generate_nginx_uri_mappings(
            ctx.parent.params['archive_host'],
            ctx.parent.params['openstax_host'],
            book,
        )
        write_nginx_map(book_uri_map, out=output)


def generate_cnx_uris(book_id):
    """\
    Generates a list of URIs for a cnx book. The URIs are several variations
    of the same page. This includes URIs with and without versions
    that use both the long and short id as well as the combination of the two.

    """
    nodes = list(get_book_nodes(book_id))
    book_node = nodes[0]

    short_book_id = book_node['short_id']

    for node in nodes[1:]:  # skip the book
        # Non-versioned URIs
        yield f"/contents/{book_id}:{node['id']}/{node['slug']}"
        yield f"/contents/{book_id}:{node['short_id']}/{node['slug']}"
        yield f"/contents/{book_node['short_id']}:{node['id']}/{node['slug']}"
        yield f"/contents/{book_node['short_id']}:{node['short_id']}/{node['slug']}"
        # Partial versioned URIs
        yield f"/contents/{book_id}@1.1:{node['id']}/{node['slug']}"
        yield f"/contents/{book_id}@2.99:{node['short_id']}/{node['slug']}"
        yield f"/contents/{book_node['short_id']}@15.123:{node['id']}/{node['slug']}"
        yield f"/contents/{book_node['short_id']}@0.0:{node['short_id']}/{node['slug']}"
        # Fully versioned URIs
        yield f"/contents/{book_id}@1.1:{node['id']}@2/{node['slug']}"
        yield f"/contents/{book_id}@2.99:{node['short_id']}@0/{node['slug']}"
        yield f"/contents/{book_node['short_id']}@15.123:{node['id']}@999/{node['slug']}"
        yield f"/contents/{book_node['short_id']}@0.0:{node['short_id']}@654321/{node['slug']}"




@click.command()
@click.option('-o', '--output', type=click.File(mode='w'))
@click.pass_context
def generate_cnx_uris_for_rex_books(ctx, output):
    """This outputs a list of CNX URIs to stdout.
    These are URIs that should redirect to REX.

    The URIs output by this function are intended for testing use.
    They exercise a number of variations the URI can be represented as.

    """
    release_json_url = get_rex_release_json_url(ctx.parent.params['openstax_host'])
    release_data = requests.get(release_json_url).json()
    for book in release_data['books']:
        for uri in generate_cnx_uris(book):
            output.write(uri + '\n')


@click.group()
@click.option('--openstax-host', envvar='OPENSTAX_HOST', default='openstax.org')
@click.option('--archive-host', envvar='ARCHIVE_HOST', default='archive.cnx.org')
def main(*args, **kwargs):
    pass


main.add_command(update_rex_redirects)
main.add_command(generate_cnx_uris_for_rex_books)


if __name__ == '__main__':
    main()
