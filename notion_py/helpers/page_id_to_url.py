def page_id_to_url(page_id: str, print_now=False):
    page_id = page_id.replace('-', '')
    url = 'https://www.notion.so/dyhn/' + page_id
    if print_now:
        print(url)
    return url


if __name__ == '__main__':
    page_id_to_url('cc794772-ba90-4c52-8c06-bafd24a613f0', print_now=True)
