import re
from datetime import date

from django import forms
from django.core.exceptions import ValidationError

from .models import Person

# Inline error messages (Pashto). The same texts are used in person_form.js.
REQ = "دا ډګر اړین دی."
DUP = "دا د تذکرې شمېره مخکې ثبت شوې ده."
BAD_ID = "د تذکرې شمېره سمه نه ده (۵ تر ۳۰ توري، شمېرې یا - /)."
BAD_PHONE = "د تلیفون شمېره سمه نه ده. بېلګه: 0700123456"
BAD_DOB = "د زېږېدو نېټه سمه نه ده."
BAD_YEAR = "د فراغت کال سم نه دی."
BAD_START = "د پیل نېټه نشي کولی راتلونکې وي."
PHOTO_TYPE = "عکس باید JPG، PNG یا WEBP وي."
PHOTO_SIZE = "د عکس اندازه باید له 2 MB څخه کمه وي."


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ["full_name", "father_name", "grandfather_name", "date_of_birth", "id_number",
                  "phone", "email", "address", "photo", "degree", "institution",
                  "graduation_year", "job_title", "organization", "start_date", "notes"]
        error_messages = {"id_number": {"unique": DUP}}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.error_messages.update(required=REQ, invalid="دا معلومات سم نه دي.",
                                    max_length="دا متن ډېر اوږد دی.", invalid_image=PHOTO_TYPE)
        self.fields["email"].error_messages["invalid"] = "بریښنالیک سم نه دی."

    def clean_id_number(self):
        v = self.cleaned_data["id_number"].strip()
        if not re.fullmatch(r"[0-9A-Za-z/\-]{5,30}", v):
            raise ValidationError(BAD_ID)
        return v

    def clean_phone(self):
        v = re.sub(r"[\s\-()]", "", self.cleaned_data["phone"])
        if not re.fullmatch(r"\+?\d{9,15}", v):
            raise ValidationError(BAD_PHONE)
        return v

    def clean_date_of_birth(self):
        v = self.cleaned_data["date_of_birth"]
        if v > date.today() or v.year < 1900:
            raise ValidationError(BAD_DOB)
        return v

    def clean_graduation_year(self):
        v = self.cleaned_data["graduation_year"]
        if v is not None and not (1950 <= v <= date.today().year + 6):
            raise ValidationError(BAD_YEAR)
        return v

    def clean_start_date(self):
        v = self.cleaned_data["start_date"]
        if v and v > date.today():
            raise ValidationError(BAD_START)
        return v

    def clean_photo(self):
        img = self.cleaned_data.get("photo")
        if img:
            if img.size > 2 * 1024 * 1024:
                raise ValidationError(PHOTO_SIZE)
            fmt = getattr(getattr(img, "image", None), "format", None)
            if fmt not in ("JPEG", "PNG", "WEBP"):
                raise ValidationError(PHOTO_TYPE)
        return img
