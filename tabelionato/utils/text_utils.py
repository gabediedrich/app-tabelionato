import unicodedata


def remove_accents(self, input_str):
    nfkd_form = unicodedata.normalize("NFKD", self.input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
