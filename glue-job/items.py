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
    from pyspark.sql.functions import col

    df = dfc.select(list(dfc.keys())[0]).toDF()

    item_df = (
        df.withColumn(
            "CREATION_TIMESTAMP",
            F.unix_timestamp(F.to_timestamp(col("CREATION_TIMESTAMP"))),
        )
        .withColumn(
            "Exclude",
            F.when(
                (col("Sponsored") == 1)
                | (col("Section") == "life/horoscopes")
                | (F.concat_ws("|", col("Keywords")).contains("omit"))
                | (F.concat_ws("|", col("Keywords")).contains("zerocanada")),
                1,
            ).otherwise(0),
        )
        .select(
            col("ITEM_ID"),
            col("CREATION_TIMESTAMP"),
            col("ContentText"),
            col("Category"),
            col("WordCount"),
            col("Exclude"),
        )
        .filter(
            col("CREATION_TIMESTAMP")
            > F.unix_timestamp(F.date_sub(F.current_date(), 14))
        )
        .repartition(1)
    )

    item_df = item_df.na.drop(subset=["ITEM_ID", "CREATION_TIMESTAMP", "ContentText"])

    dyf_dmy = DynamicFrame.fromDF(item_df, glueContext, "custom_transform")

    return DynamicFrameCollection({"CustomTransform0": dyf_dmy}, glueContext)


args = getResolvedOptions(sys.argv, ["JOB_NAME"])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args["JOB_NAME"], args)

# Script generated for node Amazon DynamoDB
AmazonDynamoDB_node1634784260002 = glueContext.create_dynamic_frame.from_catalog(
    database="tgam-personalize-content-metadata",
    table_name="sophi3contentmetadata",
    transformation_ctx="AmazonDynamoDB_node1634784260002",
)

# Script generated for node ApplyMapping
ApplyMapping_node1634784508894 = ApplyMapping.apply(
    frame=AmazonDynamoDB_node1634784260002,
    mappings=[
        ("keywords", "array", "Keywords", "array"),
        ("category", "string", "Category", "string"),
        ("section", "string", "Section", "string"),
        ("contenttext", "string", "ContentText", "string"),
        ("wordcount", "long", "WordCount", "long"),
        ("contentid", "string", "ITEM_ID", "string"),
        ("publisheddate", "string", "CREATION_TIMESTAMP", "string"),
        ("sponsored", "boolean", "Sponsored", "int"),
    ],
    transformation_ctx="ApplyMapping_node1634784508894",
)

# Script generated for node Custom transform
Customtransform_node1635182473882 = MyTransform(
    glueContext,
    DynamicFrameCollection(
        {"ApplyMapping_node1634784508894": ApplyMapping_node1634784508894}, glueContext
    ),
)

# Script generated for node SelectFromCollection
SelectFromCollection_node1635182720846 = SelectFromCollection.apply(
    dfc=Customtransform_node1635182473882,
    key=list(Customtransform_node1635182473882.keys())[0],
    transformation_ctx="SelectFromCollection_node1635182720846",
)

# Script generated for node Items
Items_node1634784630336 = glueContext.write_dynamic_frame.from_options(
    frame=SelectFromCollection_node1635182720846,
    connection_type="s3",
    format="csv",
    connection_options={
        "path": "s3://tgam-personalize-dev-1950aa20/glue-job/Items/",
        "partitionKeys": [],
    },
    transformation_ctx="Items_node1634784630336",
)

job.commit()
