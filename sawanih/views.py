import csv
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.http.multipartparser import MultiPartParserError
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_http_methods, require_POST

from .forms import PersonForm
from .models import COMPLETE, Person

PAGE_SIZE = 25
REPORT_PAGE_SIZE = 50
_LATIN = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def _json(data, status=200):
    return JsonResponse(data, status=status, json_dumps_params={"ensure_ascii": False})


def _errors(form):
    return {field: msgs[0] for field, msgs in form.errors.items()}


# ----------------------------------------------------------- query helpers
def _search(qs, text):
    """Name / father name / ID / phone / organization contains the text (Pashto digits accepted)."""
    text = (text or "").strip()
    if not text:
        return qs
    cond = Q()
    for t in {text, text.translate(_LATIN)}:
        cond |= (Q(full_name__icontains=t) | Q(father_name__icontains=t) | Q(id_number__icontains=t)
                 | Q(phone__icontains=t) | Q(organization__icontains=t))
    return qs.filter(cond)


def _date(value):
    try:
        return parse_date(value or "")
    except ValueError:          # well-formed but impossible, e.g. 2026-02-31
        return None


def _filtered(params):
    """Shared by the Reports page and the CSV export so both always agree."""
    qs = _search(Person.objects.select_related("created_by"), params.get("q"))
    d_from, d_to = _date(params.get("date_from")), _date(params.get("date_to"))
    if d_from:
        qs = qs.filter(created_at__date__gte=d_from)
    if d_to:
        qs = qs.filter(created_at__date__lte=d_to)
    status = params.get("status")
    if status == "complete":
        qs = qs.filter(COMPLETE)
    elif status == "incomplete":
        qs = qs.filter(~COMPLETE)
    return qs


# ------------------------------------------------------------------- pages
@login_required
def dashboard(request):
    q = request.GET.get("q", "").strip()
    page = Paginator(_search(Person.objects.all(), q), PAGE_SIZE).get_page(request.GET.get("page"))
    return render(request, "sawanih/dashboard.html", {"active": "home", "page_obj": page, "q": q})


@login_required
def person_new(request):
    return render(request, "sawanih/person_form.html", {"active": "add", "person": None})


@login_required
def person_edit(request, pk):
    return render(request, "sawanih/person_form.html",
                  {"active": "home", "person": get_object_or_404(Person, pk=pk)})


@login_required
def person_detail(request, pk):
    person = get_object_or_404(Person.objects.select_related("created_by", "updated_by"), pk=pk)
    return render(request, "sawanih/person_detail.html", {"active": "home", "p": person})


# ----------------------------------------------------------------- reports
@login_required
def reports(request):
    qs = _filtered(request.GET)
    stats = qs.aggregate(total=Count("id"), complete=Count("id", filter=COMPLETE))
    stats["incomplete"] = stats["total"] - stats["complete"]
    page = Paginator(qs, REPORT_PAGE_SIZE).get_page(request.GET.get("page"))
    return render(request, "sawanih/reports.html",
                  {"active": "reports", "page_obj": page, "stats": stats, "f": request.GET})


def _cell(value):
    """Stop Excel from running a cell as a formula (=, @, or +/- followed by text)."""
    s = "" if value is None else str(value)
    if s and (s[0] in "=@\t\r" or (s[0] in "+-" and not re.fullmatch(r"[+\-]?[\d\s()\-]+", s))):
        return "'" + s
    return s


@login_required
def reports_export(request):
    qs = _filtered(request.GET)
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="persons-{timezone.localdate():%Y-%m-%d}.csv"'
    resp.write("﻿")        # BOM so Excel reads Pashto text correctly
    w = csv.writer(resp)
    w.writerow(["بشپړ نوم", "د پلار نوم", "د نیکه نوم", "د زېږېدو نېټه", "د تذکرې شمېره", "تلیفون",
                "بریښنالیک", "پته", "درجه", "موسسه", "د فراغت کال", "دنده", "اداره", "د پیل نېټه",
                "حالت", "د ثبت نېټه", "ثبت کوونکی"])
    for p in qs.iterator():
        w.writerow([_cell(x) for x in (
            p.full_name, p.father_name, p.grandfather_name, p.date_of_birth, p.id_number, p.phone,
            p.email, p.address, p.degree, p.institution, p.graduation_year, p.job_title, p.organization,
            p.start_date, "بشپړ" if p.is_complete else "نابشپړ",
            timezone.localtime(p.created_at).strftime("%Y-%m-%d %H:%M"),
            p.created_by.get_username() if p.created_by else "")])
    return resp


# --------------------------------------------------------------------- API
@login_required
@require_POST
def api_person_create(request):
    """POST /api/persons/  — multipart form data, photo optional."""
    form = PersonForm(request.POST, request.FILES)
    if not form.is_valid():
        return _json({"errors": _errors(form)}, 400)
    person = form.save(commit=False)
    person.created_by = request.user            # audit: who ...
    person.save()                               # ... and when (created_at is automatic)
    messages.success(request, "شخص په بریالیتوب ثبت شو.")
    return _json({"id": person.pk}, 201)


@login_required
@require_http_methods(["PUT", "DELETE"])
def api_person_item(request, pk):
    """PUT /api/persons/<id>/ updates a person; DELETE /api/persons/<id>/ removes one."""
    person = get_object_or_404(Person, pk=pk)

    if request.method == "DELETE":
        if not request.user.has_perm("sawanih.delete_person"):
            return _json({"error": "تاسو د ړنګولو اجازه نه لرئ."}, 403)
        photo_name, storage = person.photo.name, person.photo.storage
        person.delete()
        if photo_name:
            storage.delete(photo_name)
        messages.success(request, "ریکارډ ړنګ شو.")
        return _json({"ok": True})

    # PUT: Django only parses multipart bodies for POST, so parse it by hand (keeps photo upload working).
    if request.content_type != "multipart/form-data":
        return _json({"error": "bad request"}, 400)
    try:
        data, files = request.parse_file_upload(request.META, request)
    except MultiPartParserError:
        return _json({"error": "bad request"}, 400)

    old_photo = person.photo.name               # read BEFORE the form touches the instance
    form = PersonForm(data, files, instance=person)   # instance => unique-ID check ignores this person
    if not form.is_valid():
        return _json({"errors": _errors(form)}, 400)
    person = form.save(commit=False)
    person.updated_by = request.user
    person.save()
    if old_photo and "photo" in files and old_photo != person.photo.name:
        person.photo.storage.delete(old_photo)  # drop the replaced file
    messages.success(request, "د شخص معلومات په بریالیتوب تازه شول.")
    return _json({"id": person.pk})
