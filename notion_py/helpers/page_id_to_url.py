def page_id_to_url(page_id: str, print_now=False):
    page_id = page_id.replace('-', '')
    url = 'https://www.notion.so/dyhn/' + page_id
    if print_now:
        print(url)
    return url


if __name__ == '__main__':
    page_id_to_url('961d1ca0a3d24a46b838ba85e710f18d', print_now=True)
