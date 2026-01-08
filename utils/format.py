def format_currency(amount):
    if amount is None or amount == 0:
        return ""
    return "{:,}".format(amount).replace(",", ".")


def parse_currency(text):
    if not text:
        return 0
    return int("".join(c for c in text if c.isdigit()) or 0)


def format_money(event):
    widget = event.widget

    # Lấy text hiện tại
    text = widget.get()

    # Parse về số
    number = parse_currency(text)

    # Format lại
    formatted = format_currency(number)

    # Nếu giống nhau thì thôi
    if text == formatted:
        return

    # Update text
    widget.delete(0, "end")
    widget.insert(0, formatted)

    # 👉 QUAN TRỌNG: luôn đặt con trỏ về cuối
    widget.icursor("end")
