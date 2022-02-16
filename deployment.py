import configparser
import os
import sys
import time

import boto3
import botocore

ROOT_DIR_PATH = os.path.dirname(os.path.abspath(__file__))

session = boto3.session.Session(profile_name=sys.argv[1]) if len(sys.argv) > 1 else boto3.session.Session
s3 = session.resource('s3')

def create_template_storage_bucket(bucket_name):
    # This bucket needs to be private probably.
    response = s3.create_bucket(
        Bucket=bucket_name,

    )
    print(response)
    return True

def check_for_template_storage_bucket(bucket_name):
    # Requires 'General' and 'S3' config
    try:
        response = s3.meta.client.head_bucket(Bucket=bucket_name)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print("Storage Bucket exists.")
            return True

    except botocore.exceptions.ClientError as e:

        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            print("Bucket Does Not Exist. \n")
            print("I will create bucket for you")

            response = create_template_storage_bucket(bucket_name)
            print(response)
            return True
        elif error_code == 403:
            print("Private Bucket. Forbidden Access!")
            return False


def upload_cf_templates_to_s3(bucket_name):
    s3_client = session.client('s3')
    for root, dirs, files in os.walk('templates'):
        for file in files:
            try:
                s3_client.upload_file(os.path.join(root, file), bucket_name, file)
            except botocore.exceptions.ClientError as e:
                print(e)
                return False

    return True


def deploy(config, template_storage_bucket_name):


    BUILD_DIR = os.path.join(ROOT_DIR_PATH, "build_artifact")

    STACK_NAME = "%s-%s-%s" % (
        config['General']['env'],
        config['General']['identifier'],
        config['CloudFormation']['main_stack_name']
    )

    parameters_override_string = "Environment=%s TemplateStorageBucket=%s" % (
        config['General']['env'],
        template_storage_bucket_name
    )

    if not os.path.exists(BUILD_DIR):
        os.mkdir(BUILD_DIR)


    for root, dirs, files in os.walk('templates'):
        for file in files:

            dir_name = file.split(".")[0]

            print(os.path.join(BUILD_DIR, dir_name))

            try:
                os.system(
                    "sam build --build-dir %s --template %s --base-dir %s -u" % (
                        os.path.join(BUILD_DIR, dir_name),
                        os.path.join(ROOT_DIR_PATH, f"templates/{file}"),
                        ROOT_DIR_PATH
                    )
                )

            except botocore.exceptions.ClientError as e:
                print(e)
                return False



    # os.system(
    #     "sam build --build-dir %s -u" % (
    #         BUILD_DIR
    #     )
    # )

    print("******************** SAM BUILD DONE ********************")

    # os.system(
    #     "sam package --template-file %s --output-template-file %s --resolve-s3 %s" % (
    #         os.path.join(BUILD_DIR, "template.yaml"),
    #         os.path.join(BUILD_DIR, "packaged.yaml"),
    #         "--profile %s" % ("vcatak-main") #TODO: REMOVE HARDCODE
    #     )
    # )
    #
    # for root, dirs, files in os.walk('templates'):
    #     for file in files:
    #         try:
    #             os.system(
    #                 "sam package --template-file %s --output-template-file %s --resolve-s3 %s" % (
    #                     os.path.join(BUILD_DIR, file),
    #                     os.path.join(BUILD_DIR, f"packaged-{file}"),
    #                     "--profile %s" % ("vcatak-main")  # TODO: REMOVE HARDCODE
    #                 )
    #             )
    #         except botocore.exceptions.ClientError as e:
    #             print(e)

    print("******************** SAM PACKAGE DONE ********************")

    capabilities = "CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND"

    os.system(
        "sam deploy  --template-file %s --stack-name %s --capabilities %s --parameter-overrides %s --region %s %s" % (
            os.path.join(BUILD_DIR, "packaged.yaml"),
            STACK_NAME,
            capabilities,
            parameters_override_string,
            "us-east-1", #TODO: REMOVE HARDCODE
            "--profile %s" % ("vcatak-main") #TODO: REMOVE HARDCODE
        )
    )

    print("******************** SAM DEPLOY DONE ********************")


def main(config):

    # - Get Template Storage Bucket name from configuration
    template_storage_bucket_name = "-".join([
        config['General']['env'],
        config['General']['identifier'],
        config['S3']['template_storage_bucket_name']
    ])

    if check_for_template_storage_bucket(template_storage_bucket_name):

        if upload_cf_templates_to_s3(template_storage_bucket_name):

            deploy(config, template_storage_bucket_name)


if __name__ == "__main__":
    # - check if Config ini exists
    #     - No  -> throw exception
    #     - Yes -> Read configuration and invoke MAIN function
    if not os.path.exists('deployment.ini'):
        raise FileNotFoundError("'deployment.ini' file not found - can't proceed with deployment.")

    config = configparser.ConfigParser()
    config.read('deployment.ini')

    main(config)
