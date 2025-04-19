import subprocess

def deploy_rapp_with_helm(chart_path: str, release_name: str, namespace: str):
    """
    Deploys a rApp Helm chart to the specified Kubernetes namespace.

    Args:
        chart_path (str): Path to the Helm chart (.tgz file).
        release_name (str): Desired name for the Helm release.
        namespace (str): Kubernetes namespace where the rApp will be deployed.
    """
    try:
        command = [
            "helm", "install", release_name,
            chart_path,
            f"--namespace={namespace}"
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("✅ rApp deployed successfully:\n", result.stdout)
    except subprocess.CalledProcessError as e:
        print("❌ Failed to deploy rApp:\n", e.stderr)

# Example usage:
# helm install a1-rapp ./a1rapp-0.1.0.tgz --namespace=nonrtric
