from django.contrib.auth.views import (LoginView,
                                       LogoutView,
                                       PasswordChangeDoneView,
                                       PasswordChangeView,
                                       PasswordResetView,
                                       PasswordResetDoneView,
                                       PasswordResetConfirmView,
                                       PasswordResetCompleteView)


from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path('logout/',
         LogoutView.as_view(template_name='users/logged_out.html'),
         name='logout'
         ),
    # когда кто-то вышел из своей учетной записи
    path('login/',
         LoginView.as_view(template_name='users/login.html'),
         name='login'
         ),
    path('signup/', views.SignUp.as_view(), name='signup'),
    # cтраница регистрации нового пользователя
    # Смена пароля: задать новый пароль
    path('password_change/',
         PasswordChangeView.as_view(
             template_name='users/password_change_form.html'),
         name='password_change'
         ),
    # Смена пароля: уведомление об удачной смене пароля
    path('password_change/done/',
         PasswordChangeDoneView.as_view(
             template_name='users/password_change_done.html'),
         name='password_change_done'
         ),
    # Восстановление пароля:  форма восст. через email
    path(
        'password_reset/',
        PasswordResetView.as_view(
            template_name='users/password_reset_form.html'),
        name='password_reset_form'),
    # Восстановление пароля: уведомление об отправке ссылки для
    # восстановления пароля на email
    path(
        'password_reset/done/',
        PasswordResetDoneView.as_view(
            template_name='users/password_reset_done.html'),
        name='password_reset_done'),
    # Восстановление пароля: уведомление о том,что пароль изменен
    path(
        'reset/done/',
        PasswordResetCompleteView.as_view(
            template_name='users/password_reset_complete.html'),
        name='password_reset_complete'),
    # Восстановление пароля: страница подтверждения сброса пароля
    # пользователь попадает сюда по ссылек из письма
    path(
        'reset/<uidb64>/<token>/',
        PasswordResetConfirmView.as_view(
            template_name='users/password_reset_confirm.html'),
        name='password_reset_confirm'),
]
