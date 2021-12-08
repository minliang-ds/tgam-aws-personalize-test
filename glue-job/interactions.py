import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrameCollection
from awsglue.dynamicframe import DynamicFrame

# Script generated for node Custom transform
def MyTransform(glueContext, dfc) -> DynamicFrameCollection:
    from pyspark.sql import functions as F
    from pyspark.sql.functions import explode, col

    df = dfc.select(list(dfc.keys())[0]).toDF()

    main_keys = ["timestamp", "datetime_collector_local", "eventdate", "datetime_local"]

    keys = (
        df.select(explode("eventAttributes"))
        .select("key")
        .distinct()
        .rdd.flatMap(lambda x: x)
        .collect()
    )

    exprs = [col("eventAttributes").getItem(k).alias(k) for k in keys]
    exprs.extend(main_keys)

    df = df.select(*exprs)

    isp_badlist = [
        "Amazon.com",
        "Amazon",
        "Googlebot",
        "Digital Ocean",
        "The Globe and Mail",
    ]

    url_badlist = [
        "localhost",
        "sandbox.tgam.arcpublishing.com",
        "arc-local.theglobeandmail.com",
        "arc-dev.theglobeandmail.com",
        "origin-arc-dev.tgam.arcpublishing.com",
        "origin-sandbox.tgam.arcpublishing.com",
        "preview-subscribe.theglobeandmail.com",
        "stg-subscribe.theglobeandmail.com",
    ]

    int_df = (
        df.withColumn(
            "USER_ID",
            F.when(col("sp_user_id").isNotNull(), col("sp_user_id")).otherwise(
                col("sp_domain_userid")
            ),
        )
        .withColumn(
            "TIMESTAMP", F.unix_timestamp(F.to_timestamp(col("sp_derived_tstamp")))
        )
        .select(
            col("USER_ID"),
            col("content_contentid").alias("ITEM_ID"),
            col("TIMESTAMP"),
            col("sp_event_name").alias("EVENT_TYPE"),
            col("visitor_type"),
            col("visitor_countrycode"),
            col("device_detector_visitorplatform"),
            col("device_detector_brandname"),
            col("device_detector_browserfamily"),
        )
        .filter(col("TIMESTAMP") > F.unix_timestamp(F.date_sub(F.current_date(), 7)))
        .filter(col("sp_app_id") == "theglobeandmail-website")
        .filter(col("sp_event_name") == "page_view")
        .filter(col("page_type") == "article")
        .filter(col("content_contentid").isNotNull())
        .filter(~col("content_contentid").contains("http"))
        .filter(
            ~(col("device_detector_visitorplatform") == "Bot")
            | (col("device_detector_visitorplatform").isNull())
        )
        .filter(
            ~(col("visitor_servicecode").contains("PREMIUM~PREMIUM~~~~~"))
            | (col("visitor_servicecode").isNull())
        )
        .filter(~(col("sp_ip_isp").isin(isp_badlist)) | (col("sp_ip_isp").isNull()))
        .filter(
            ~(col("sp_page_urlhost").isin(url_badlist))
            | (col("sp_page_urlhost").isNull())
        )
        .orderBy(["USER_ID", "TIMESTAMP"])
        .repartition(1)
    )

    int_df = int_df.na.drop(subset=["USER_ID", "ITEM_ID", "TIMESTAMP", "EVENT_TYPE"])

    dyf_dmy = DynamicFrame.fromDF(int_df, glueContext, "custom_transform")

    return DynamicFrameCollection({"CustomTransform0": dyf_dmy}, glueContext)


args = getResolvedOptions(sys.argv, ["JOB_NAME"])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# Script generated for node Sophi AUX
SophiAUX_node1634742939009 = glueContext.create_dynamic_frame.from_catalog(
    database="tgam-personalize-sophi-aux",
    push_down_predicate="year == year(current_date) AND ((month == month(current_date)-1 AND day > day(current_date)) OR (month == month(current_date) AND day <= day(current_date)))",
    table_name="sophi3_batch_data",
    transformation_ctx="SophiAUX_node1634742939009",
)

# Script generated for node Custom transform
Customtransform_node1634745956841 = MyTransform(
    glueContext,
    DynamicFrameCollection(
        {"SophiAUX_node1634742939009": SophiAUX_node1634742939009}, glueContext
    ),
)

# Script generated for node SelectFromCollection
SelectFromCollection_node1634746373083 = SelectFromCollection.apply(
    dfc=Customtransform_node1634745956841,
    key=list(Customtransform_node1634745956841.keys())[0],
    transformation_ctx="SelectFromCollection_node1634746373083",
)

# Script generated for node Amazon S3
AmazonS3_node1634746525938 = glueContext.getSink(
    path="s3://tgam-personalize-dev-1950aa20/glue-job/Interactions/",
    connection_type="s3",
    updateBehavior="UPDATE_IN_DATABASE",
    partitionKeys=[],
    enableUpdateCatalog=True,
    transformation_ctx="AmazonS3_node1634746525938",
)
AmazonS3_node1634746525938.setCatalogInfo(
    catalogDatabase="tgam-personalize-sophi-aux",
    catalogTableName="tgam-personalize-interactions",
)
AmazonS3_node1634746525938.setFormat("csv")
AmazonS3_node1634746525938.writeFrame(SelectFromCollection_node1634746373083)
job.commit()
