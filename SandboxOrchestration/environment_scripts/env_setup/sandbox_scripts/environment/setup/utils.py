def validate_all_apps_deployed(deploy_results):
    if deploy_results is not None:
        for deploy_res in deploy_results.ResultItems:
            if not deploy_res.Success:
                raise Exception("Reservation is Active with Errors - " + deploy_res.Error)