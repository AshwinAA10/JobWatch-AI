#!/usr/bin/env python3
"""Validate production environment configuration without printing sensitive credentials."""

import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.config import Settings


def main() -> int:
    print("=" * 60)
    print("JobWatch AI — Production Configuration Validator")
    print("=" * 60)

    try:
        settings = Settings()
    except Exception as exc:
        print(f"❌ Failed to parse environment settings: {exc}")
        return 1

    print(f"Environment:       {settings.APP_ENV}")
    print(f"Debug Mode:        {settings.DEBUG}")
    print(f"App Version:       {settings.APP_VERSION}")
    print(f"Database Config:   {'Configured' if settings.DATABASE_URL else 'MISSING'}")
    print(f"JWT Secret:        {'Configured (>=32 chars)' if len(settings.JWT_SECRET) >= 32 else 'WEAK/DEFAULT'}")
    print(f"CORS Origins:      {len(settings.CORS_ORIGINS)} origin(s) configured")
    print(f"OpenAI Key:        {'Configured' if settings.OPENAI_API_KEY else 'Not set (AI disabled/fallback)'}")
    print(f"Email Provider:    {settings.EMAIL_PROVIDER if settings.EMAIL_NOTIFICATIONS_ENABLED else 'Disabled'}")
    print(f"Monitoring:        {'Enabled' if settings.MONITORING_ENABLED else 'Disabled'}")
    print(f"Rate Limiting:     {'Enabled' if settings.RATE_LIMIT_ENABLED else 'Disabled'}")
    print("-" * 60)

    if settings.APP_ENV.lower() in ("production", "prod"):
        try:
            settings.validate_production_configuration()
            print("[PASS] Production validation PASSED. Configuration is safe for deployment.")
            return 0
        except RuntimeError as exc:
            print(f"[FAIL] Production validation FAILED:\n{exc}")
            return 1
    else:
        print("[INFO] Non-production environment. Strict production validation skipped.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
