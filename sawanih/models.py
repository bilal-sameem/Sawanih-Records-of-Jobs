from django.conf import settings
from django.db import models
from django.db.models import Q


class SawanihEntry(models.Model):
    slug = models.SlugField("slug", unique=True, allow_unicode=True)
    title = models.CharField("نوم / سرلیک", max_length=200)
    subtitle = models.CharField("لنډه معرفي", max_length=300, blank=True)
    intro = models.TextField("پېژندنه", blank=True)
    language = models.CharField("ژبه", max_length=5, default="ps")
    published = models.BooleanField("خپور شوی", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "سوانح"
        verbose_name_plural = "سوانح"

    def __str__(self):
        return self.title


class EntrySection(models.Model):
    entry = models.ForeignKey(SawanihEntry, on_delete=models.CASCADE, related_name="sections")
    heading = models.CharField("سرلیک", max_length=200)
    body = models.TextField("متن", blank=True)
    position = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        ordering = ["position", "id"]


class TimelineEvent(models.Model):
    entry = models.ForeignKey(SawanihEntry, on_delete=models.CASCADE, related_name="events")
    date_label = models.CharField("نېټه", max_length=60)
    title = models.CharField("پېښه", max_length=200)
    description = models.TextField("تشریح", blank=True)
    position = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        ordering = ["position", "id"]


class EntryQuote(models.Model):
    entry = models.ForeignKey(SawanihEntry, on_delete=models.CASCADE, related_name="quotes")
    text = models.TextField("وینا")
    attribution = models.CharField("منسوب", max_length=200, blank=True)
    position = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        ordering = ["position", "id"]


# "Complete" record = education AND job details are filled in.
# Used for the status filter in Reports and the status badge.
COMPLETE = ~Q(degree="") & ~Q(institution="") & ~Q(job_title="") & ~Q(organization="")


class Person(models.Model):
    # --- شخصي معلومات ---
    full_name = models.CharField("بشپړ نوم", max_length=150)
    father_name = models.CharField("د پلار نوم", max_length=150)
    grandfather_name = models.CharField("د نیکه نوم", max_length=150, blank=True)
    date_of_birth = models.DateField("د زېږېدو نېټه")
    id_number = models.CharField("د تذکرې شمېره", max_length=30, unique=True)
    phone = models.CharField("تلیفون", max_length=20)
    email = models.EmailField("بریښنالیک", blank=True)
    address = models.TextField("پته", blank=True)
    photo = models.ImageField("عکس", upload_to="persons/%Y/", blank=True)
    # --- تحصیلي معلومات ---
    degree = models.CharField("درجه", max_length=100, blank=True)
    institution = models.CharField("موسسه", max_length=150, blank=True)
    graduation_year = models.PositiveSmallIntegerField("د فراغت کال", null=True, blank=True)
    # --- دندې معلومات ---
    job_title = models.CharField("دنده", max_length=150, blank=True)
    organization = models.CharField("اداره", max_length=150, blank=True)
    start_date = models.DateField("د پیل نېټه", null=True, blank=True)
    # --- اضافي ---
    notes = models.TextField("یادښتونه / سوانح", blank=True)
    # --- audit log ---
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "شخص"
        verbose_name_plural = "اشخاص"

    @property
    def is_complete(self):
        return all([self.degree, self.institution, self.job_title, self.organization])

    def __str__(self):
        return self.full_name
