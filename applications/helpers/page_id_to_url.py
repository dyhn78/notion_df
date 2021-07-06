def page_id_to_url(page_id: str, print_now=False):
    page_id = page_id.replace('-', '')
    url = 'https://www.notion.so/dyhn/' + page_id
    if print_now:
        print(url)
    return url


if __name__ == '__main__':
    page_id_to_url('83ea05ba-7228-43c3-a830-57779e5a00a1', print_now=True)
