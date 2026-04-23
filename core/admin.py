from django.contrib import admin

from .models import ClaimMissingMiles, MemberProfile, MilesTransaction, StaffProfile, User

admin.site.register(User)
admin.site.register(MemberProfile)
admin.site.register(StaffProfile)
admin.site.register(MilesTransaction)
admin.site.register(ClaimMissingMiles)
