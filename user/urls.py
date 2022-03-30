from django.contrib.auth import views as auth_views
from django.urls import include, path

from . import views

app_name = "user"

urlpatterns = [
    path("accounts/login/", views.accounts_login, name="accounts_login"),  # 장고 URL -> 로그인 템플릿 연결 버튼
    path("sign-up/", views.sign_up_view, name="sign-up"),
    path("sign-in/", views.sign_in_view, name="sign-in"),
    path("logout/", views.logout, name="logout"),
    # =============== user profile update ================ #
    path("profile_edit/<int:id>", views.profile_edit, name="profile_edit"),
    path("password/", views.password, name="password"),
    path("api_update_user_image", views.api_update_user_image, name="api_update_user_image"),
    path("my_page/<int:id>", views.user_my_page, name="user_my_page"),
]
