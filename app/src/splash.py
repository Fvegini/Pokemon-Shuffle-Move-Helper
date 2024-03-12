def close_splash():
    try:
        import pyi_splash
        pyi_splash.close()
    except:
        return