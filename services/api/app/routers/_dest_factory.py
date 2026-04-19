from cdp_shared.models.activation import Destination


def get_destination_instance(dest: Destination):
    from services.activation.app.destinations.sendgrid import SendGridDestination
    from services.activation.app.destinations.sms_esms import ESMSDestination
    from services.activation.app.destinations.meta_ads import MetaAdsDestination

    MAP = {
        "sendgrid": SendGridDestination,
        "sms_esms": ESMSDestination,
        "meta_ads": MetaAdsDestination,
    }
    cls = MAP.get(dest.type)
    if not cls:
        raise ValueError(f"Unknown destination type: {dest.type}")
    return cls(dest.config)
