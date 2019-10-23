

__all__ = (
    "prompt",
    "prompt_bool",
)


no_value = object()


def required(value):
    if not value:
        raise ValueError()
    return value


def prompt(question, default=no_value, default_show=None, validator=required, **kwargs):
    """
    Prompt for a value from the command line. A default value can be provided,
    which will be used if no text is entered by the user. The value can be
    validated, and possibly changed by supplying a validator function. Any
    extra keyword arguments to this function will be passed along to the
    validator. If the validator raises a ValueError, the error message will be
    printed and the user asked to supply another value.
    """
    if default_show:
        question += f" [{default_show}] "
    elif default and default is not no_value:
        question += f" [{default}] "
    else:
        question += " "

    while True:
        resp = input(question)
        if not resp:
            if default is None:
                return None
            if default is not no_value:
                resp = default

        try:
            return validator(resp, **kwargs)
        except ValueError as e:
            if str(e):
                print(str(e))


def prompt_bool(question, default=False, yes="y", no="n"):
    please_answer = f' Please answer "{yes}" or "{no}"'

    def validator(value):
        if value:
            value = str(value).lower()[0]
        if value == yes:
            return True
        elif value == no:
            return False
        else:
            raise ValueError(please_answer)

    if default is None:
        default = no_value
        default_show = yes + "/" + no
    elif default:
        default = yes
        default_show = yes.upper() + "/" + no
    else:
        default = no
        default_show = yes + "/" + no.upper()

    return prompt(
        question, default=default, default_show=default_show, validator=validator
    )
