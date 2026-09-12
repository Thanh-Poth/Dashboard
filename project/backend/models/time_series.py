    
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller
from sklearn.metrics import mean_absolute_error, mean_squared_error
import pmdarima as pm
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.datasets import load_wine
from sklearn.metrics import accuracy_score, classification_report
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score
from models.classifiers import Classifiers

class ARIMA(Classifiers):

    def check_stationarity(self, df : pd.DataFrame):
        result = adfuller(df, autolag='AIC')
        p_value = result[1]
        print(f'ADF Statistic: {result[0]}')
        print(f'p-value: {p_value}')
        print('Stationary' if p_value < 0.05 else 'Non-Stationary')


    def sarima_model_selected(self):
        p, d, q = 1, 1, 1 #
        P, D, Q, s = 1, 1, 1, 12 #
        self.check_stationarity(self.df['Close'])

        split_ratio = 0.8
        split_index = int(len(self.df) * split_ratio)
        
        train_data = self.df.iloc[:split_index]
        test_data = self.df.iloc[split_index:]


        model = SARIMAX(train_data['Close'], order=(p, d, q), seasonal_order=(P, D, Q, s))
        results = model.fit()
        forecast_periods = len(test_data)
        

        forecast = results.forecast(steps=forecast_periods)

        plt.figure(figsize=(10, 6))
        plt.plot(test_data.index, test_data['Close'], label='Observed')
        plt.plot(test_data.index, forecast, label='Forecast', color='red')
        plt.title("Sales Forecast")
        plt.xlabel("Date")
        plt.ylabel("Sales")
        plt.legend()
        plt.show()

        mae = mean_absolute_error(test_data['Close'], forecast)
        mse = mean_squared_error(test_data['Close'], forecast)
        
        print("MAE:", mae)
        print("MSE:", mse)

        modele_optimise = pm.auto_arima(
            y = train_data['Close'], 
            seasonal=True,       
            m=12,                
            d=None, D=None,      
            start_p=0, start_q=0,
            max_p=100, max_q=100,    
            start_P=0, start_Q=0,
            max_P=100, max_Q=100,
            trace=True,          
            error_action='ignore',
            suppress_warnings=True, 
            stepwise=True        
        )

        forecast_periods = len(test_data)
        forecast = results.forecast(steps=forecast_periods)
        mae = mean_absolute_error(test_data['Close'], forecast)
        mse = mean_squared_error(test_data['Close'], forecast)

        print("MAE:", mae)
        print("MSE:", mse)
        self.df["SARIMA_pred"] = results
        print(modele_optimise.summary())

        forecast_opti = modele_optimise.predict(n_periods=forecast_periods)
        
        # Alignement de l'index de la prédiction avec test_data pour faciliter les calculs
        forecast_opti.index = test_data.index 

        print("\n--- Modèle Optimisé ---")
        print("MAE:", mean_absolute_error(test_data['Close'], forecast_opti))
        print("MSE:", mean_squared_error(test_data['Close'], forecast_opti))
        
        # Sauvegarde des prédictions dans le DataFrame
        self.df.loc[test_data.index, "SARIMA_pred"] = forecast_opti

        # --- 3. ANALYSE DE LA PENTE / TENDANCE ---
        # .diff() calcule la différence entre la valeur à t et t-1
        actual_diff = test_data['Close'].diff()
        pred_diff = forecast_opti.diff()

        # Comparaison des signes (-1 pour baisse, 1 pour hausse). 
        # Si les signes sont identiques, le modèle a eu raison sur la direction.
        correct_trend = (np.sign(actual_diff) == np.sign(pred_diff))

        # Extraction des dates correctes et incorrectes (en ignorant le premier point qui est NaN à cause de diff())
        correct_trend = correct_trend.dropna()
        correct_dates = correct_trend[correct_trend == True].index
        incorrect_dates = correct_trend[correct_trend == False].index

        # Graphique de l'analyse de tendance
        plt.figure(figsize=(12, 6))
        plt.plot(test_data.index, test_data['Close'], label='Réel (Close)', color='black', alpha=0.5, linewidth=2)
        plt.plot(test_data.index, forecast_opti, label='Prédiction Optimisée', color='orange', alpha=0.7)

        # Ajout de points verts pour les bonnes pentes et rouges pour les mauvaises
        plt.scatter(correct_dates, test_data.loc[correct_dates, 'Close'], 
                    color='green', label='Tendance Correcte', zorder=5, s=40)
        plt.scatter(incorrect_dates, test_data.loc[incorrect_dates, 'Close'], 
                    color='red', label='Tendance Incorrecte', zorder=5, s=40, marker='x')

        # Calcul du pourcentage de réussite (Directional Accuracy)
        accuracy = (len(correct_dates) / len(correct_trend)) * 100

        plt.title(f"Évaluation de la Direction (Pente) - Précision : {accuracy:.2f}%")
        plt.xlabel("Date")
        plt.ylabel("Prix (Close)")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.show()