from telegram.error import BadRequest


async def safe_edit_message(
    query,
    text,
    reply_markup=None,
    parse_mode=None,
):
    try:

        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )

    except BadRequest as e:

        if "Message is not modified" in str(e):
            return

        raise