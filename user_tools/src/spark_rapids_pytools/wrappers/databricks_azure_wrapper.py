# Copyright (c) 2023, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Wrapper class to run tools associated with RAPIDS Accelerator for Apache Spark plugin on DATABRICKS_AZURE."""

from spark_rapids_pytools.cloud_api.sp_types import DeployMode, CloudPlatform
from spark_rapids_pytools.common.utilities import ToolLogging
from spark_rapids_pytools.rapids.qualification import QualFilterApp, QualificationAsLocal, QualGpuClusterReshapeType


class CliDBAzureLocalMode:  # pylint: disable=too-few-public-methods
    """
    A wrapper that runs the RAPIDS Accelerator tools locally on the dev machine for DATABRICKS_AZURE.
    """

    @staticmethod
    def qualification(cpu_cluster: str,
                      eventlogs: str = None,
                      profile: str = None,
                      local_folder: str = None,
                      remote_folder: str = None,
                      gpu_cluster: str = None,
                      tools_jar: str = None,
                      credentials_file: str = None,
                      filter_apps: str = QualFilterApp.tostring(QualFilterApp.SAVINGS),
                      gpu_cluster_recommendation: str = QualGpuClusterReshapeType.tostring(
                          QualGpuClusterReshapeType.get_default()),
                      jvm_heap_size: int = 24,
                      verbose: bool = False,
                      **rapids_options) -> None:
        """
        The Qualification tool analyzes Spark events generated from CPU based Spark applications to
        help quantify the expected acceleration and costs savings of migrating a Spark application
        or query to GPU. The wrapper downloads dependencies and executes the analysis on the local
        dev machine.
        :param cpu_cluster: The Databricks-cluster on which the Spark applications were executed. The argument
                can be a Databricks-cluster or a valid path to the cluster's properties file (json format)
                generated by the databricks-CLI.
        :param  eventlogs: Event log filenames or ABFS (Azure Blob File System) storage directories
                containing event logs (comma separated). If missing, the wrapper reads the Spark's
                property `spark.eventLog.dir` defined in `cpu_cluster`. This property should be included
                in the output of `databricks clusters get [--cluster-id CLUSTER_ID| --cluster-name CLUSTER_NAME]`.
                Note that the wrapper will raise an exception if the property is not set.
        :param profile: A named Databricks profile to get the settings/credentials of the Databricks CLI.
        :param local_folder: Local work-directory path to store the output and to be used as root
                directory for temporary folders/files. The final output will go into a subdirectory called
                ${local_folder}/qual-${EXEC_ID} where exec_id is an auto-generated unique identifier of the
                execution. If the argument is NONE, the default value is the env variable
                RAPIDS_USER_TOOLS_OUTPUT_DIRECTORY if any; or the current working directory.
        :param remote_folder: An ABFS (Azure Blob File System) folder where the output is uploaded at the end
                of execution. If no value is provided, the output will be only available on local disk.
        :param gpu_cluster: The Databricks-cluster on which the Spark applications are planned to be migrated.
                The argument can be a Databricks-cluster or a valid path to the cluster's properties file
                (json format) generated by the databricks-CLI. If missing, the wrapper maps the databricks machine
                instances of the original cluster into databricks instances that support GPU acceleration.
        :param tools_jar: Path to a bundled jar including Rapids tool. The path is a local filesystem,
                or remote ABFS url. If missing, the wrapper downloads the latest rapids-4-spark-tools_*.jar
                from maven repo.
        :param credentials_file: The local path of JSON file that contains the application credentials.
               If missing, the wrapper looks for "DATABRICKS_CONFIG_FILE" environment variable
               to provide the location of a credential file. The default credentials file exists as
               "~/.databrickscfg" on Unix, Linux, or macOS
        :param filter_apps: filtering criteria of the applications listed in the final STDOUT table
                is one of the following (NONE, SPEEDUPS, SAVINGS).
                Note that this filter does not affect the CSV report.
                "NONE" means no filter applied. "SPEEDUPS" lists all the apps that are either
                'Recommended', or 'Strongly Recommended' based on speedups. "SAVINGS"
                lists all the apps that have positive estimated GPU savings except for the apps that
                are "Not Applicable".
        :param gpu_cluster_recommendation: The type of GPU cluster recommendation to generate.
               It accepts one of the following ("CLUSTER", "JOB" and the default value "MATCH").
                "MATCH": keep GPU cluster same number of nodes as CPU cluster;
                "CLUSTER": recommend optimal GPU cluster by cost for entire cluster;
                "JOB": recommend optimal GPU cluster by cost per job
        :param verbose: True or False to enable verbosity to the wrapper script.
        :param jvm_heap_size: The maximum heap size of the JVM in gigabytes.
        :param rapids_options: A list of valid Qualification tool options.
                Note that the wrapper ignores ["output-directory", "platform"] flags, and it does not support
                multiple "spark-property" arguments.
                For more details on Qualification tool options, please visit
                https://nvidia.github.io/spark-rapids/docs/spark-qualification-tool.html#qualification-tool-options
        """
        if verbose:
            # when debug is set to true set it in the environment.
            ToolLogging.enable_debug_mode()
        wrapper_qual_options = {
            'platformOpts': {
                # the databricks profile
                'profile': profile,
                'credentialFile': credentials_file,
                'deployMode': DeployMode.LOCAL,
            },
            'migrationClustersProps': {
                'cpuCluster': cpu_cluster,
                'gpuCluster': gpu_cluster
            },
            'jobSubmissionProps': {
                'remoteFolder': remote_folder,
                'platformArgs': {
                    'jvmMaxHeapSize': jvm_heap_size
                }
            },
            'eventlogs': eventlogs,
            'filterApps': filter_apps,
            'toolsJar': tools_jar,
            'gpuClusterRecommendation': gpu_cluster_recommendation
        }
        QualificationAsLocal(platform_type=CloudPlatform.DATABRICKS_AZURE,
                             cluster=None,
                             output_folder=local_folder,
                             wrapper_options=wrapper_qual_options,
                             rapids_options=rapids_options).launch()


class DBAzureWrapper:  # pylint: disable=too-few-public-methods
    """
    A wrapper script to run RAPIDS Accelerator tools (Qualification, Profiling, and Bootstrap) on Databricks_Azure.
    """

    def __init__(self):
        self.qualification = CliDBAzureLocalMode.qualification
