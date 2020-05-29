from typing import List

from d3m import index
from d3m.metadata.base import ArgumentType
from d3m.metadata.pipeline import Pipeline, PrimitiveStep

from primitives.pipeline_base import PipelineBase

class DeepARPipeline(PipelineBase):

    def __init__(
        self, 
        epochs: int = 50,
        steps_per_epoch: int = 100,
        number_samples: int = 100,
        prediction_length: int = 30,
        context_length: int = 30,
        quantiles: List[float] = [0.1, 0.9],
        group_compose: bool = False,
        confidence_intervals: bool = False,
    ):

        pipeline_description = Pipeline()
        pipeline_description.add_input(name="inputs")

        # DS to DF on input DS
        step = PrimitiveStep(
            primitive=index.get_primitive(
                "d3m.primitives.data_transformation.dataset_to_dataframe.Common"
            )
        )
        step.add_argument(
            name="inputs", argument_type=ArgumentType.CONTAINER, data_reference="inputs.0"
        )
        step.add_output("produce")
        pipeline_description.add_step(step)

        # Simple Profiler Column Role Annotation
        step = PrimitiveStep(
            primitive=index.get_primitive("d3m.primitives.schema_discovery.profiler.Common")
        )
        step.add_argument(
            name="inputs",
            argument_type=ArgumentType.CONTAINER,
            data_reference="steps.0.produce",
        )
        step.add_output("produce")
        pipeline_description.add_step(step)

        # column parser on input DF
        step = PrimitiveStep(
            primitive=index.get_primitive(
                "d3m.primitives.data_transformation.column_parser.Common"
            )
        )
        step.add_argument(
            name="inputs",
            argument_type=ArgumentType.CONTAINER,
            data_reference="steps.1.produce",
        )
        step.add_output("produce")
        step.add_hyperparameter(
            name="parse_semantic_types",
            argument_type=ArgumentType.VALUE,
            data=[
                "http://schema.org/Boolean",
                "http://schema.org/Integer",
                "http://schema.org/Float",
                "https://metadata.datadrivendiscovery.org/types/FloatVector",
                "http://schema.org/DateTime",
            ],
        )
        pipeline_description.add_step(step)

        # group compose
        if group_compose:
            step = PrimitiveStep(
                primitive=index.get_primitive(
                    "d3m.primitives.data_transformation.grouping_field_compose.Common"
                )
            )
            step.add_argument(
                name="inputs",
                argument_type=ArgumentType.CONTAINER,
                data_reference="steps.2.produce",
            )
            step.add_output("produce")
            pipeline_description.add_step(step)

        # parse attribute semantic types
        step = PrimitiveStep(
            primitive=index.get_primitive(
                "d3m.primitives.data_transformation.extract_columns_by_semantic_types.Common"
            )
        )
        data_ref = "steps.3.produce" if group_compose else "steps.2.produce"
        step.add_argument(
            name="inputs",
            argument_type=ArgumentType.CONTAINER,
            data_reference=data_ref,
        )
        step.add_hyperparameter(
            name="semantic_types",
            argument_type=ArgumentType.VALUE,
            data=["https://metadata.datadrivendiscovery.org/types/Attribute"],
        )
        step.add_output("produce")
        pipeline_description.add_step(step)

        # # Step 4: imputer
        # step = PrimitiveStep(
        #     primitive=index.get_primitive("d3m.primitives.data_cleaning.imputer.SKlearn")
        # )
        # step.add_argument(
        #     name="inputs",
        #     argument_type=ArgumentType.CONTAINER,
        #     data_reference="steps.3.produce",
        # )
        # step.add_output("produce")
        # step.add_hyperparameter(
        #     name="return_result", argument_type=ArgumentType.VALUE, data="replace"
        # )
        # step.add_hyperparameter(
        #     name="use_semantic_types", argument_type=ArgumentType.VALUE, data=True
        # )
        # pipeline_description.add_step(step)

        # parse target semantic types
        step = PrimitiveStep(
            primitive=index.get_primitive(
                "d3m.primitives.data_transformation.extract_columns_by_semantic_types.Common"
            )
        )
        data_ref = "steps.3.produce" if group_compose else "steps.2.produce"
        step.add_argument(
            name="inputs",
            argument_type=ArgumentType.CONTAINER,
            data_reference=data_ref,
        )
        step.add_hyperparameter(
            name="semantic_types",
            argument_type=ArgumentType.VALUE,
            data=[
                "https://metadata.datadrivendiscovery.org/types/Target",
                "https://metadata.datadrivendiscovery.org/types/TrueTarget",
                "https://metadata.datadrivendiscovery.org/types/SuggestedTarget",
            ],
        )
        step.add_output("produce")
        pipeline_description.add_step(step)

        # forecasting primitive
        step = PrimitiveStep(
            primitive=index.get_primitive(
                "d3m.primitives.time_series_forecasting.lstm.DeepAR"
            )
        )
        data_ref = "steps.4.produce" if group_compose else "steps.3.produce"
        step.add_argument(
            name="inputs",
            argument_type=ArgumentType.CONTAINER,
            data_reference=data_ref,
        )
        data_ref = "steps.5.produce" if group_compose else "steps.4.produce"
        step.add_argument(
            name="outputs",
            argument_type=ArgumentType.CONTAINER,
            data_reference=data_ref,
        )
        step.add_hyperparameter(
            name="epochs",
            argument_type=ArgumentType.VALUE,
            data=epochs,
        )
        step.add_hyperparameter(
            name="steps_per_epoch",
            argument_type=ArgumentType.VALUE,
            data=steps_per_epoch,
        )
        step.add_hyperparameter(
            name="number_samples",
            argument_type=ArgumentType.VALUE,
            data=number_samples,
        )
        step.add_hyperparameter(
            name="prediction_length",
            argument_type=ArgumentType.VALUE,
            data=prediction_length,
        )
        step.add_hyperparameter(
            name="context_length",
            argument_type=ArgumentType.VALUE,
            data=context_length,
        )
        step.add_hyperparameter(
            name="quantiles",
            argument_type=ArgumentType.VALUE,
            data=quantiles,
        )
        
        if confidence_intervals:
            step.add_output("produce_confidence_intervals")
            pipeline_description.add_step(step)
            
            data_ref = "steps.6.produce" if group_compose else "steps.5.produce"
            pipeline_description.add_output(
                name="output predictions", data_reference=data_ref
            )

        else:
            step.add_output("produce")
            pipeline_description.add_step(step)

            # construct predictions
            step = PrimitiveStep(
                primitive=index.get_primitive(
                    "d3m.primitives.data_transformation.construct_predictions.Common"
                )
            )
            data_ref = "steps.6.produce" if group_compose else "steps.5.produce"
            step.add_argument(
                name="inputs",
                argument_type=ArgumentType.CONTAINER,
                data_reference=data_ref,
            )
            step.add_argument(
                name="reference",
                argument_type=ArgumentType.CONTAINER,
                data_reference="steps.1.produce",
            )
            step.add_output("produce")
            pipeline_description.add_step(step)

            data_ref = "steps.7.produce" if group_compose else "steps.6.produce"
            pipeline_description.add_output(
                name="output predictions", data_reference=data_ref
            )

        self.pipeline = pipeline_description