def page_id_to_url(page_id: str, print_now=False):
    page_id = page_id.replace('-', '')
    url = 'https://www.notion.so/dyhn/' + page_id
    if print_now:
        print(url)
    return url


def page_url_to_id(page_url: str):
    if '-' not in page_url[-32:]:
        return page_url[-32:]
    return page_url[-36:].replace('-', '')


if __name__ == '__main__':
    page_id_to_url('961d1ca0a3d24a46b838ba85e710f18d', print_now=True)
