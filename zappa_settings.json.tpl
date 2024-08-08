{
    "dev": {
        "app_function": "application.application",
        "profile_name": "default",
        "project_name": "smartcdss-api",
        "runtime": "python3.8",
        "s3_bucket": "$SMARTCDSS_ZAPPA_BUCKET",
        "profile_name": "$SMARTCDSS_ZAPPA_PROFILE",
	    "slim_handler":true,
        "use_precompiled_packages":true, 
        "includes":["libmysqlclient"],
        "environment_variables": {
            "SMARTCDSS_SECRET_TOKEN": "$SMARTCDSS_SECRET_TOKEN"
        }
    }
}
