from evidently import Report
from evidently.presets import DataDriftPreset
import pandas as pd
import json
import os
import logging

logging.basicConfig(    
    filename='app.log', 
    filemode='a', # 'a' to append logs, 'w' to overwrite every run
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    level=logging.INFO # Capture INFO, WARNING, ERROR, and CRITICAL
    )
logger=logging.getLogger("monitor")

def run_drift(
        output_path:str= os.getenv('DRIFT_RESULTS_FILE'),
        run_id:str= None
    ) -> None:
    """ Run drift detection between reference and current data """
    ref=pd.read_csv(os.getenv("TRAINING_DATA_FILE"))
    #logger.info(ref.columns)
    curr=pd.read_csv(os.getenv("TRACK_INPUT_IN_FILE"))
    #logger.info(curr.columns)

    report=Report(metrics=[DataDriftPreset()])
    report.run(reference_data=ref, current_data=curr)
    
    #Debug info
    logger.info(f"report: {dir(report)}")
    logger.info(f"available methods: {[m for m in dir(report) if not m.startswith('_')]}")
    drift_summary=None

  # Method 1: Try accessing report._inner_suite.results (for older versions)
    try:
        if hasattr(report, '_inner_suite') and hasattr(report._inner_suite, 'results'):
            results = report._inner_suite.results
            logger.info(" Successfully accessed _inner_suite.results")
            drift_summary = extract_drift_from_results(results)
    except Exception as e:
        logger.info(f"_inner_suite.results access failed: {e}")
    
    # Method 2: Try accessing the actual computed metrics (not the preset)
    if drift_summary is None:
        try:
            logger.info("Trying to access computed metrics from _inner_suite...")
            if hasattr(report, '_inner_suite'):
                suite = report._inner_suite
                logger.info(f"Suite type: {type(suite)}")
                logger.info(f"Suite attributes: {[attr for attr in dir(suite) if not attr.startswith('_')]}")
                
                # Check if suite has metrics (computed results)
                if hasattr(suite, 'metrics'):
                    logger.info(f"Found {len(suite.metrics)} computed metrics")
                    for i, metric in enumerate(suite.metrics):
                        logger.info(f"Metric {i}: {type(metric)}")
                        logger.info(f"Metric {i} attributes: {[attr for attr in dir(metric) if not attr.startswith('_')]}")
                        
                        # Try to get result from computed metric
                        if hasattr(metric, 'get_result'):
                            try:
                                result = metric.get_result()
                                logger.info(f" Got result from computed metric {i}: {type(result)}")
                                drift_summary = create_drift_summary_from_result(result)
                                break
                            except Exception as e:
                                logger.info(f"Failed to get result from metric {i}: {e}")
                        elif hasattr(metric, 'result'):
                            try:
                                result = metric.result
                                logger.info(f" Got result from computed metric {i}: {type(result)}")
                                drift_summary = create_drift_summary_from_result(result)
                                break
                            except Exception as e:
                                logger.info(f"Failed to access result from metric {i}: {e}")
                                
        except Exception as e:
            logger.info(f"Computed metrics access failed: {e}")
    
    # Method 3: Try expanding the preset to get actual metrics
    if drift_summary is None:
        try:
            logger.info("Trying to expand DataDriftPreset to get actual metrics...")
            if hasattr(report, 'metrics') and report.metrics:
                preset = report.metrics[0]  # This is the DataDriftPreset
                if hasattr(preset, 'generate_metrics'):
                    # Try to get the actual metrics from the preset
                    actual_metrics = preset.generate_metrics()
                    logger.info(f" Generated {len(actual_metrics)} metrics from preset")
                    
                    # Look for DataDriftTable metric specifically
                    for metric in actual_metrics:
                        logger.info(f"Generated metric type: {type(metric)}")
                        metric_name = str(type(metric)).lower()
                        if 'datadrift' in metric_name and 'table' in metric_name:
                            logger.info(f" Found DataDriftTable metric: {type(metric)}")
                            # This metric should be in the computed suite
                            break
                            
        except Exception as e:
            logger.info(f"Preset expansion failed: {e}")
    
    # Method 4: Try accessing specific metric types from computed suite
    if drift_summary is None:
        try:
            logger.info("Looking for specific drift metrics in computed suite...")
            if hasattr(report, '_inner_suite') and hasattr(report._inner_suite, 'metrics'):
                for i, metric in enumerate(report._inner_suite.metrics):
                    metric_name = str(type(metric)).lower()
                    logger.info(f"Checking metric {i}: {type(metric)}")
                    
                    # Look for DataDriftTable or similar
                    if 'datadrift' in metric_name:
                        logger.info(f" Found drift metric: {type(metric)}")
                        try:
                            if hasattr(metric, 'get_result'):
                                result = metric.get_result()
                            elif hasattr(metric, 'result'):
                                result = metric.result
                            else:
                                continue
                                
                            logger.info(f" Successfully extracted result from {type(metric)}")
                            drift_summary = create_drift_summary_from_result(result)
                            break
                            
                        except Exception as e:
                            logger.info(f"Failed to extract from {type(metric)}: {e}")
                            continue
                            
        except Exception as e:
            logger.info(f"Specific metric search failed: {e}")
    
    # Method 5: Try to force calculation and then extract
    if drift_summary is None:
        try:
            logger.info("Trying to force calculation...")
            # Try to trigger internal calculation
            if hasattr(report, '_inner_suite'):
                suite = report._inner_suite
                if hasattr(suite, 'calculate'):
                    suite.calculate()
                    logger.info(" Called suite.calculate()")
                    
                # Now try to access results again
                if hasattr(suite, 'results'):
                    drift_summary = extract_drift_from_results(suite.results)
                elif hasattr(suite, 'metrics'):
                    for metric in suite.metrics:
                        if hasattr(metric, 'get_result'):
                            result = metric.get_result()
                            drift_summary = create_drift_summary_from_result(result)
                            break
                        elif hasattr(metric, 'result'):
                            result = metric.result
                            drift_summary = create_drift_summary_from_result(result)
                            break
                            
        except Exception as e:
            logger.info(f"Force calculation failed: {e}")
    
    # Method 6: Try newer Evidently API methods
    if drift_summary is None:
        try:
            logger.info("Trying newer Evidently API methods...")
            
            # Try as_dict() method
            if hasattr(report, 'as_dict'):
                result_dict = report.as_dict()
                logger.info(f" Got report as dict: {type(result_dict)}")
                if 'metrics' in result_dict:
                    for metric_data in result_dict['metrics']:
                        if 'result' in metric_data:
                            drift_summary = create_drift_summary_from_result(metric_data['result'])
                            break
            
            # Try json() method
            elif hasattr(report, 'json'):
                import json as json_lib
                result_json = report.json()
                result_dict = json_lib.loads(result_json)
                logger.info(f" Got report as JSON")
                if 'metrics' in result_dict:
                    for metric_data in result_dict['metrics']:
                        if 'result' in metric_data:
                            drift_summary = create_drift_summary_from_result(metric_data['result'])
                            break
                            
        except Exception as e:
            logger.info(f"Newer API methods failed: {e}")
    
    # Method 7: Manual calculation approach
    if drift_summary is None:
        try:
            logger.info("Trying manual calculation approach...")
            # Create a new DataDriftTable metric and run it manually
            from evidently.metrics import DataDriftTable
            
            manual_metric = DataDriftTable()
            
            # Try to calculate manually
            if hasattr(manual_metric, 'calculate'):
                manual_metric.calculate(reference_data=ref, current_data=cur)
                logger.info(" Manual calculation completed")
                
                if hasattr(manual_metric, 'get_result'):
                    result = manual_metric.get_result()
                    drift_summary = create_drift_summary_from_result(result)
                elif hasattr(manual_metric, 'result'):
                    result = manual_metric.result
                    drift_summary = create_drift_summary_from_result(result)
                    
        except ImportError:
            logger.info("DataDriftTable not available for manual import")
        except Exception as e:
            logger.info(f"Manual calculation failed: {e}")

    # Fallback: Create minimal structure
    if drift_summary is None:
        logger.info("All extraction methods failed, creating minimal structure")
        drift_summary = {
            "dataset_drift": None,
            "number_of_drifted_features": 0,
            "share_of_drifted_features": 0.0,
            "metrics_list": [],
            "error": "Could not extract detailed drift metrics from Evidently report",
            "report_generated": True,
            "evidently_version_issue": True
        }

    # Save results
    with open(output_path, "w") as f:
        json.dump(drift_summary, f, indent=2)
    logger.info(f"Drift summary saved to {output_path}")
    
    # Also print summary to console
    logger.info(f"Drift Summary:")
    logger.info(f"Dataset drift detected: {drift_summary.get('dataset_drift', 'Unknown')}")
    logger.info(f"Drifted features: {drift_summary.get('number_of_drifted_features', 0)}")
    logger.info(f"Drift percentage: {drift_summary.get('share_of_drifted_features', 0.0):.2%}")
    return drift_summary

def extract_drift_from_results(results):
    """ extract drift info from results object"""
    logger.info(f"Extracting from results: {results}")

    try:
        if isinstance(results,list) and len(results) > 0:
            first_result=results[0]
        elif isinstance(results, dict):
            first_result=results
        else:
            raise ValueError(f"Unexpected results type : {type(results)}")
        
        logger.info(f"Creating drift summary from results: {first_result}")
        return create_drift_summary_from_result(first_result)
    except Exception as e:
        raise RuntimeError(f"Could not parse results") 


def create_drift_summary_from_result(result) -> dict:
    """ Create drift summary from any result object or dict"""
    def safe_get(obj,key,default=None):
        if isinstance(obj, dict):
            return obj.get(key,default)
        elif hasattr(obj, key):
            return getattr(obj,key,default)
        else:
            return default

        #Print available attributes for debugging
        if hasattr(result, '__dict__'):
            logger.info(f"Result attributes: {list(result.__dict__.keys())}")
        elif isinstance(result, dict):
            logger.info(f"result keys : {list(result.keys())}")
        
        #try to extract drift info
        drift_summary={
            "dataset_drift": safe_get(result, "dataset_drift", None),
            "number_of_drifted_features": safe_get(result, "number_of_drifted_features",0),
            "share_of_drifted_features": safe_get(result, "share_of_drifted_features", 0.0),
            "metrics_list": []
        }

        #try to get feature-level drift info
        drift_by_columns= safe_get(result, "drift_by_columns",{})
        if drift_by_columns and isinstance(drift_by_columns,dict):
            for feature_name, feature_data in drift_by_columns.items():
                drift_summary["metrics_list"].append({
                    "feature_name": feature_name,
                    "drift_score": safe_get(feature_data, "drift_score", 0.0),
                    "drift_detected": safe_get(feature_data, "drift_detected", False),


                })
        return drift_summary

if __name__ == "__main__":
    logger.info("🚀 Starting drift detection...")
    run_drift()