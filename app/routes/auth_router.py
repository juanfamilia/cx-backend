@router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(get_db),
):
    user = await get_user_by_email(session, form_data.username)

    if not user or not verify_password(
        form_data.password,
        user.hashed_password,
    ):
        raise InvalidCredentialsException()

    if user.deleted_at:
        raise DisabledException("Usuario desactivado o eliminado")

    # Verificar pago SOLO si el usuario es válido
    await check_company_payment_status(user, session)

    # Asegurar onboarding (NO romper login si falla)
    try:
        await OnboardingService.ensure_exists(
            user_id=user.id,
            company_id=user.company_id,
            session=session,
        )
    except Exception:
        # Log silencioso aceptable en login
        pass

    public_user = UserPublic.model_validate(user)

    access_token = create_access_token(
        user.email,
        timedelta(days=settings.JWT_EXPIRE),
    )

    return {
        "access_token": access_token,
        "user": public_user,
    }
