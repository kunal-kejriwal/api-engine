PLAN_RECORD_LIMITS = {
    "FREE": 100,
    "BASE": 5000,
    "PRO": 20000,
    "ENTERPRISE": 100000,
}

QUOTA_MODELS = [
    "core.ProductCatalog",
    "core.CustomerProfile",
    "core.OrderTransaction",
    "core.FeatureUsageAnalytics",
    #"core.CustomObject"
]

QUOTA_MODEL_OWNERSHIP = {
    "core.ProductCatalog": "created_by",
    "core.CustomerProfile": "user",
    "core.OrderTransaction": "created_by",
    "core.FeatureUsageAnalytics": "user",
    "core.CustomObject": "tenant",
}


PLAN_CUSTOM_OBJECT_LIMITS = {
    "FREE": {
        "max_objects": 2,
        "max_fields_per_object": 5,
        "max_records_per_object": 100,
    },
    "BASE": {
        "max_objects": 5,
        "max_fields_per_object": 15,
        "max_records_per_object": 1000,
    },
    "PRO": {
        "max_objects": 20,
        "max_fields_per_object": 50,
        "max_records_per_object": 10000,
    },
    "ENTERPRISE": {
        "max_objects": 20,
        "max_fields_per_object": 50,
        "max_records_per_object": 10000,
    },
}