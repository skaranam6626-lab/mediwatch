# mediwatch

The automated pipeline performs these steps on every code change:

1. **Environment Setup**: Install dependencies
2. **Data Pipeline**: Download and preprocess Kaggle dataset
3. **Model Training**: Train model with MLflow tracking
4. **Artifact Storage**: Save models and experiment logs
5. **Quality Assurance**: Ensure reproducible results

**Workflow Triggers:**
- Push to main branch
- Pull requests
- Manual trigger

**What gets tracked:**
- Model performance metrics
- Training parameters
- Data preprocessing steps
- Model artifacts

---

## 📊 Model Performance Tracking

The pipeline tracks these metrics automatically:
- **Accuracy**: Overall prediction accuracy
- **Precision**: True positive rate
- **Recall**: Sensitivity
- **F1-Score**: Harmonic mean of precision and recall

All metrics are logged to MLflow for experiment comparison.


## Run below scripts to test model 

$HOME_PATH : is uppermost parent directory of the project. Defaults to current directory. Ensure all child folders are under this directory.

# download the dataset
    ./scripts/download.sh

#run preprocessing
    ./scripts/run_preprocessing.sh

#run trainer
    ./scripts/run_trainer.sh

#run webapp
    ./scripts/run_webApp.sh
