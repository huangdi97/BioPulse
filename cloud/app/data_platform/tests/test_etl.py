from cloud.app.data_platform.etl.pipeline import ETLPipeline
from cloud.app.data_platform.schemas.data_platform import PipelineRunStatus


class TestETLPipeline:
    def test_add_task_and_topological_order(self):
        pipeline = ETLPipeline(name="test_pipeline")
        pipeline.add_task("a", "Task A", lambda ctx: ctx)
        pipeline.add_task("b", "Task B", lambda ctx: ctx, upstream=["a"])
        pipeline.add_task("c", "Task C", lambda ctx: ctx, upstream=["a"])
        pipeline.add_task("d", "Task D", lambda ctx: ctx, upstream=["b", "c"])

        order = pipeline._topological_order()
        assert order[0] == "a"
        assert order.index("b") < order.index("d")
        assert order.index("c") < order.index("d")

    def test_topological_order_cycle_detection(self):
        pipeline = ETLPipeline(name="cycle_test")
        pipeline.add_task("x", "Task X", lambda ctx: ctx, upstream=["y"])
        pipeline.add_task("y", "Task Y", lambda ctx: ctx, upstream=["x"])
        try:
            pipeline._topological_order()
            assert False, "Expected ValueError for cycle"
        except ValueError:
            pass

    def test_topological_order_unknown_upstream(self):
        pipeline = ETLPipeline(name="bad_dep")
        pipeline.add_task("a", "Task A", lambda ctx: ctx, upstream=["nonexistent"])
        try:
            pipeline._topological_order()
            assert False, "Expected ValueError for unknown upstream"
        except ValueError:
            pass

    def test_run_with_defaults_produces_success(self):
        pipeline = ETLPipeline(name="default_test")
        result = pipeline.run()
        assert result.pipeline_name == "default_test"
        assert result.status == PipelineRunStatus.SUCCESS
        assert result.processed_rows >= 1
        assert len(result.task_results) == 3
        task_names = [t["name"] for t in result.task_results]
        assert "Extract from data source" in task_names
        assert "Apply dbt-style transformations" in task_names
        assert "Load into warehouse" in task_names

    def test_run_with_custom_source_and_loader(self):
        pipeline = ETLPipeline(name="custom_source_test")
        pipeline.add_source(
            "crm",
            lambda: [
                {"tenant_id": "t1", "product_id": "p1", "visit_count": 3},
                {"tenant_id": "t2", "product_id": "p2", "visit_count": 5},
            ],
        )
        loaded_rows = []
        pipeline.add_loader("warehouse", lambda rows: loaded_rows.extend(rows) or len(rows))
        pipeline.define_standard_pipeline()
        result = pipeline.run()
        assert result.status == PipelineRunStatus.SUCCESS
        assert result.processed_rows == 2
        assert len(loaded_rows) == 2
        for row in loaded_rows:
            assert "tenant_id" in row
            assert "engagement_score" in row

    def test_run_with_task_failure(self):
        pipeline = ETLPipeline(name="failing_test")

        def failing_action(ctx):
            raise RuntimeError("simulated failure")

        pipeline.add_task("boom", "Failing Task", failing_action)
        result = pipeline.run()
        assert result.status == PipelineRunStatus.FAILED
        assert "simulated failure" in (result.error or "")

    def test_retry_on_failure(self):
        pipeline = ETLPipeline(name="retry_test")
        attempts = []

        def flaky_action(ctx):
            attempts.append(1)
            if len(attempts) < 3:
                raise RuntimeError("transient error")
            return ctx

        pipeline.add_task("retry", "Flaky Task", flaky_action, retries=3)
        result = pipeline.run()
        assert result.status == PipelineRunStatus.SUCCESS
        assert len(attempts) == 3

    def test_sample_extract(self):
        rows = ETLPipeline._sample_extract()
        assert len(rows) == 1
        row = rows[0]
        assert row["tenant_id"] == "tenant-demo"
        assert row["visit_count"] == 1
        assert row["engagement_score"] == 82.5

    def test_default_transform_normalizes_rows(self):
        rows = [{"custom_field": "value"}]
        result = ETLPipeline._default_transform(rows)
        assert len(result) == 1
        assert result[0]["tenant_id"] == "default"
        assert result[0]["visit_count"] == 0
        assert result[0]["engagement_score"] == 0.0
        assert result[0]["opportunity_amount"] == 0.0
        assert result[0]["compliance_issue_count"] == 0

    def test_define_standard_pipeline_defaults(self):
        pipeline = ETLPipeline(name="auto_define")
        assert len(pipeline.tasks) == 0
        pipeline.define_standard_pipeline()
        assert len(pipeline.tasks) == 3
        assert "extract" in pipeline.tasks
        assert "transform" in pipeline.tasks
        assert "load" in pipeline.tasks
        assert pipeline.tasks["transform"].upstream == ["extract"]
        assert pipeline.tasks["load"].upstream == ["transform"]

    def test_run_with_context(self):
        pipeline = ETLPipeline(name="context_test")
        captured_context = []

        def capture_context(ctx):
            captured_context.append(ctx)
            return ctx

        pipeline.add_task("capture", "Capture Context", capture_context)
        result = pipeline.run(context={"custom_key": "custom_value"})
        assert result.status == PipelineRunStatus.SUCCESS
        assert captured_context[0]["custom_key"] == "custom_value"
        assert "run_id" in captured_context[0]

    def test_compile_sql_transformations(self):
        pipeline = ETLPipeline(name="compile_test")
        sql_statements = pipeline.compile_sql_transformations()
        assert len(sql_statements) == 2
        assert all(isinstance(s, str) for s in sql_statements)
        assert any("stg_business_activity" in s for s in sql_statements)
        assert any("fact_business_activity_daily" in s for s in sql_statements)
