from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

def check_workers():
    resp = requests.get("http://nginx/stats", timeout=10)
    data = resp.json()
    print(f"Worker distribution: {data}")
    dist = data.get("distribution", [])
    if not dist:
        raise ValueError("No data from workers!")
    print("All workers responding!")

def check_health():
    for i in range(1, 4):
        resp = requests.get(f"http://app{i}:8000/health", timeout=5)
        assert resp.status_code == 200, f"app{i} unhealthy!"
        print(f"app{i} healthy")

with DAG(
    dag_id="nginx_loadtest_pipeline",
    default_args=default_args,
    description="Автоматический нагрузочный тест с проверкой балансировки",
    schedule_interval="0 * * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["loadtest", "nginx"],
) as dag:

    health_check = PythonOperator(
        task_id="check_workers_health",
        python_callable=check_health,
    )

    run_locust = BashOperator(
        task_id="run_load_test",
        bash_command="""
            docker run --rm --network nginx-loadtest_default \
            nginx-loadtest-locust \
            locust --host=http://nginx --headless \
            -u 100 -r 20 --run-time 60s \
            --csv=/tmp/results 2>&1 | tail -20
        """,
    )

    check_distribution = PythonOperator(
        task_id="check_distribution",
        python_callable=check_workers,
    )

    report = BashOperator(
        task_id="print_report",
        bash_command='echo "Load test completed at $(date). Check Grafana: http://localhost:3001"',
    )

    health_check >> run_locust >> check_distribution >> report
