from django.contrib import admin
from .models import SawanihEntry, EntrySection, TimelineEvent, EntryQuote, Person


class SectionInline(admin.StackedInline):
    model = EntrySection
    extra = 1


class EventInline(admin.TabularInline):
    model = TimelineEvent
    extra = 1


class QuoteInline(admin.TabularInline):
    model = EntryQuote
    extra = 0


@admin.register(SawanihEntry)
class SawanihEntryAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "published", "updated_at")
    list_filter = ("published", "language")
    search_fields = ("title", "subtitle")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [SectionInline, EventInline, QuoteInline]


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("full_name", "father_name", "id_number", "job_title", "created_by", "created_at")
    search_fields = ("full_name", "father_name", "id_number", "phone")
    readonly_fields = ("created_by", "created_at", "updated_by", "updated_at")
