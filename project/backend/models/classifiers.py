import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.pipeline import make_pipeline

from features.selection import FeatureSelector  # adapte le chemin d'import à la structure réelle du projet


class Classifiers:
    def __init__(self, df: pd.DataFrame, training_cfg: dict | None = None, selection_cfg: dict | None = None):
        t_cfg = training_cfg or {}
        s_cfg = selection_cfg or {}

        self.df = df
        self.target_col = t_cfg.get("target_col", "OC")
        random_state = t_cfg.get("random_state", 42)
        test_size = t_cfg.get("test_size", 0.33)

        df_train, df_test = train_test_split(self.df, test_size=test_size, shuffle=False)

        self.selector = FeatureSelector(
            config=s_cfg,
            target_col=self.target_col
        )
        df_train_sel = self.selector.fit_transform(df_train)
        df_test_sel = self.selector.transform(df_test)

        self.X_train = df_train_sel.drop(columns=[self.target_col])
        self.y_train = df_train_sel[self.target_col]
        self.X_test = df_test_sel.drop(columns=[self.target_col])
        self.y_test = df_test_sel[self.target_col]

        self.models = {
            "Logistic Regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, random_state=random_state)),
            "KNN": make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=3)),
            "SVM": make_pipeline(StandardScaler(), SVC(kernel="linear", random_state=random_state)),
            "Decision Tree": DecisionTreeClassifier(max_depth=5, random_state=random_state),
            "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=5, random_state=random_state),
            "Naive Bayes": GaussianNB(),
            "Gradient Boosting": GradientBoostingClassifier(n_estimators=100, learning_rate=1.0, max_depth=1, random_state=random_state)
        }

    def evaluate_model(self, model_name: str, model_instance):
        print(f"\n--- Evaluation : {model_name} ---")

        model_instance.fit(self.X_train, self.y_train)
        y_pred = model_instance.predict(self.X_test)

        print("Accuracy:", accuracy_score(self.y_test, y_pred))
        print(classification_report(self.y_test, y_pred, zero_division=0))

        accuracy = accuracy_score(self.y_test, y_pred)
        precision = precision_score(self.y_test, y_pred, average='weighted', zero_division=0)
        recall = recall_score(self.y_test, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(self.y_test, y_pred, average='weighted', zero_division=0)

        return accuracy, precision, recall, f1

    def run_all_models(self):
        results = {}
        for name, model in self.models.items():
            results[name] = self.evaluate_model(name, model)
        return results