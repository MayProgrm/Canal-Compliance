from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.admin.sites import AdminSite
from .models import CustomUser, Complaint, PrivacyNotice, ResourceItem

def _actualizador_only_has_permission(self, request):
    u = request.user
    if not u.is_active or not u.is_staff:
        return False
    if u.is_superuser:
        return True
    return u.groups.filter(name='Actualizador').exists()

AdminSite.has_permission = _actualizador_only_has_permission

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'company', 'role', 'area', 'branch', 'matricula', 'assignment_position', 'is_verified', 'is_staff')
    list_filter = ('is_verified', 'is_staff', 'is_superuser', 'is_active', 'company', 'branch')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'matricula', 'company', 'area', 'branch', 'role')
    fieldsets = UserAdmin.fieldsets + (('Información del perfil', {'fields': ('company', 'role', 'area', 'branch', 'matricula', 'employment_start', 'employment_end')}), ('Asignación de casos', {'fields': ('assignment_position',)}), ('Verificación', {'fields': ('phone_number', 'is_verified')}))

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('folio', 'name', 'email', 'status', 'created_at', 'assigned_to')
    list_filter = ('status', 'created_at', 'assigned_to')
    search_fields = ('folio', 'name', 'email', 'description')
    readonly_fields = ('folio', 'name', 'email', 'phone', 'created_at', 'updated_at')
    list_editable = ('status', 'assigned_to')
    fieldsets = (('Información del denunciante', {'fields': ('folio', 'name', 'email', 'phone')}), ('Denuncia', {'fields': ('description', 'attachment', 'status', 'response', 'assigned_to')}), ('Fechas', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}))
    pass

@admin.register(ResourceItem)
class ResourceItemAdmin(admin.ModelAdmin):
    list_display = ('kind', 'title', 'published_on', 'is_published', 'sort_order', 'updated_at')
    list_filter = ('kind', 'is_published')
    search_fields = ('title', 'description')
    ordering = ('kind', 'sort_order', '-published_on', '-updated_at')
    seed_marker_title = '__LIBRARY_SEEDED__'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(title=self.seed_marker_title)

@admin.register(PrivacyNotice)
class PrivacyNoticeAdmin(admin.ModelAdmin):
    list_display = ('company', 'is_published', 'updated_at')
    list_filter = ('is_published',)
    search_fields = ('company',)
