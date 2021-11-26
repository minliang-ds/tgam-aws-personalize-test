#!/bin/bash
Help()
{
   # Display Help
   echo "Create CodePipeline for personalize project."
   echo
   echo "Syntax: pipeline.sh [-e|t|p|b|r|d]"
   echo "options:"
   echo "-e     enviroment  dev/prod Default: dev"
   echo "-t     pipeline type api/mlops Default: env"
   echo "-p     pipeline prefix. Default: tgam-personalize"
   echo "-b     git repo branch Default: development"
   echo "-r     aws region to deploy Default: us-east-1"
   echo "-m     Mail for notification Default: noreply@example.com"
   echo "-d     Debug mode."
   echo
   echo "Example for dev:"
   echo "sh pipeline.sh -e dev -t api -p tgam-personalize -b development "
   echo "sh pipeline.sh -e dev -t mlops -p tgam-personalize -b development "
   echo "Example for prod:"
   echo "sh pipeline.sh -e prod -t api -p tgam-personalize -b prod "
   echo "sh pipeline.sh -e prod -t mlops -p tgam-personalize -b prod "

}

while getopts ":h:e:b:t:p:d:r:m" option; do
   case $option in
      h) # display Help
         Help
         exit;;
      e) # Enter a name
         arg_env=$OPTARG;;
      b) # Enter a name
         arg_branch=$OPTARG;;
      m) # Enter a name
         arg_mail=$OPTARG;;
      t) # Enter a name
         arg_type=$OPTARG;;
      p) # Enter a name
         arg_prefix=$OPTARG;;
      d) # Enter a name
         arg_debug=1;;
      d) # Enter a name
         arg_debug=$OPTARG;;
      r) # Enter a name
         arg_region=$OPTARG;;
     \?) # Invalid option
         echo "Error: Invalid option"
         exit;;
   esac
done

pipeline_type="${arg_type:-"mlops"}"
pipeline_env="${arg_env:-"dev"}"
pipeline_prefix="${arg_prfeix:-"tgam-personalize"}"
pipeline_region="${arg_region:-"us-east-1"}"
pipeline_branch="${arg_branch:-"development"}"
notification_mail="${arg_mail:-"noreply@example.com"}"

if [[ -n "${arg_debug}" ]]; then
  set +x
fi

cfn-lint pipeline.yaml
cfn_nag_scan -i pipeline.yaml || true

#hack for cross assume role
if [[ -n "${AWS_PROFILE}" ]];
then
    profile="--profile ${AWS_PROFILE}"
  else
    profile=""
fi

aws cloudformation deploy --region ${pipeline_region} ${profile} \
  --capabilities CAPABILITY_IAM \
  --template pipeline.yaml \
  --stack-name ${pipeline_prefix}-${pipeline_env}-${pipeline_type}-pipeline \
  --parameter-overrides ResourcesPrefix=${pipeline_prefix} \
  Environment=${pipeline_env} \
  GitHubBranch=${pipeline_branch} \
  Email=${notification_mail} \
  PipelineType=${pipeline_type} \
  DevInputBucket="tgam-personalize-dev-1950aa20"
