# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime, timedelta
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

class GRCupAnalytics:
    """
    Real-Time Analytics Engine for GR Cup Racing Data
    Processes telemetry, lap times, and generates strategic insights
    """
    
    def __init__(self, track_name='vir', race_num=1):
        self.track_name = track_name
        self.race_num = race_num
        self.data_dir = Path(f'./{track_name}')
        
        # Load all data sources
        self.lap_times = None
        self.lap_starts = None
        self.lap_ends = None
        self.telemetry = None
        self.results = None
        self.weather = None
        self.best_laps = None
        
    def load_data(self):
        """Load all available race data"""
        try:
            # Lap timing data - try multiple naming patterns
            # Patterns: R#_trackname_lap_time.csv, trackname_lap_time_R#.csv, R#_trackname*lap_time.csv
            lap_time_file = list(self.data_dir.glob(f'R{self.race_num}_{self.track_name}_lap_time.csv'))
            if not lap_time_file:
                lap_time_file = list(self.data_dir.glob(f'{self.track_name}*lap_time_R{self.race_num}.csv'))
            if not lap_time_file:
                lap_time_file = list(self.data_dir.glob(f'R{self.race_num}_{self.track_name}*lap_time.csv'))
            if not lap_time_file:
                lap_time_file = list(self.data_dir.glob(f'*lap_time*R{self.race_num}*.csv'))
            
            if lap_time_file:
                self.lap_times = pd.read_csv(lap_time_file[0])
                print(f"  [OK] Loaded lap times: {len(self.lap_times)} records")
            else:
                print("  [WARN] Lap times file not found")
            
            # Lap start data - try multiple patterns
            lap_start_file = list(self.data_dir.glob(f'R{self.race_num}_{self.track_name}*lap_start.csv'))
            if not lap_start_file:
                lap_start_file = list(self.data_dir.glob(f'{self.track_name}*lap_start_time_R{self.race_num}.csv'))
            if not lap_start_file:
                lap_start_file = list(self.data_dir.glob(f'*lap_start*R{self.race_num}*.csv'))
            
            if lap_start_file:
                self.lap_starts = pd.read_csv(lap_start_file[0])
                print(f"  [OK] Loaded lap starts: {len(self.lap_starts)} records")
            else:
                print("  [WARN] Lap starts file not found")
            
            # Lap end data - try multiple patterns
            lap_end_file = list(self.data_dir.glob(f'R{self.race_num}_{self.track_name}*lap_end.csv'))
            if not lap_end_file:
                lap_end_file = list(self.data_dir.glob(f'{self.track_name}*lap_end_time_R{self.race_num}.csv'))
            if not lap_end_file:
                lap_end_file = list(self.data_dir.glob(f'*lap_end*R{self.race_num}*.csv'))
            
            if lap_end_file:
                self.lap_ends = pd.read_csv(lap_end_file[0])
                print(f"  [OK] Loaded lap ends: {len(self.lap_ends)} records")
            else:
                print("  [WARN] Lap ends file not found")
            
            # Calculate lap times from starts and ends
            if self.lap_starts is not None and self.lap_ends is not None:
                self.lap_times = self._calculate_lap_times()
                if self.lap_times is not None:
                    print(f"  [OK] Calculated lap times: {len(self.lap_times)} records")
            
            # Telemetry data - in long format with telemetry_name and telemetry_value
            telemetry_file = list(self.data_dir.glob(f'R{self.race_num}_{self.track_name}*telemetry*.csv'))
            if telemetry_file:
                raw_telemetry = pd.read_csv(telemetry_file[0])
                # Pivot telemetry from long to wide format for easier analysis
                self.telemetry = self._pivot_telemetry(raw_telemetry)
                print(f"  [OK] Loaded telemetry: {len(self.telemetry)} records")
            else:
                print("  [WARN] Telemetry file not found")
            
            # Results and analysis - look for Official results first
            results_file = list(self.data_dir.glob('*Official*Anonymized.CSV'))
            if not results_file:
                results_file = list(self.data_dir.glob(f'*Results*Race*{self.race_num}*Anonymized.CSV'))
            
            if results_file:
                self.results = pd.read_csv(results_file[0])
                print(f"  [OK] Loaded results: {len(self.results)} records")
            else:
                print("  [WARN] Results file not found")
            
            # Weather data
            weather_file = list(self.data_dir.glob(f'*Weather*Race*{self.race_num}*.CSV'))
            if weather_file:
                self.weather = pd.read_csv(weather_file[0])
                print(f"  [OK] Loaded weather: {len(self.weather)} records")
            else:
                print("  [WARN] Weather file not found")
            
            # Best laps
            best_laps_file = list(self.data_dir.glob(f'*Best*10*Race*{self.race_num}*.CSV'))
            if best_laps_file:
                self.best_laps = pd.read_csv(best_laps_file[0])
                print(f"  [OK] Loaded best laps: {len(self.best_laps)} records")
            else:
                print("  [WARN] Best laps file not found")
            
            print(f"[OK] Successfully loaded all data for {self.track_name.upper()} Race {self.race_num}")
            return True
            
        except Exception as e:
            print(f"[FAIL] Error loading data: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _calculate_lap_times(self):
        """Calculate lap times by matching lap_starts and lap_ends on vehicle_id and lap number"""
        try:
            # Convert timestamps to datetime for calculations
            starts = self.lap_starts.copy()
            ends = self.lap_ends.copy()
            
            starts['timestamp'] = pd.to_datetime(starts['timestamp'])
            ends['timestamp'] = pd.to_datetime(ends['timestamp'])
            
            # Merge on vehicle_id and lap
            merged = ends.merge(
                starts,
                on=['vehicle_id', 'lap'],
                suffixes=('_end', '_start'),
                how='inner'
            )
            
            # Calculate lap time (end - start)
            merged['lap_time'] = (merged['timestamp_end'] - merged['timestamp_start']).dt.total_seconds()
            
            # Select relevant columns
            result = merged[['vehicle_id', 'lap', 'lap_time', 'timestamp_end']].copy()
            result.columns = ['vehicle_id', 'lap', 'lap_time', 'timestamp']
            
            # Filter out invalid lap times (must be between 30s and 300s - typical racing lap)
            result = result[(result['lap_time'] > 30) & (result['lap_time'] < 300)]
            
            print(f"  [INFO] Merged {len(starts)} starts with {len(ends)} ends -> {len(result)} lap times")
            return result
            
        except Exception as e:
            print(f"  [WARN] Error calculating lap times: {e}")
            return None
    
    def _pivot_telemetry(self, raw_telemetry):
        """
        Convert telemetry data from long format to wide format
        
        Input format (long):
        vehicle_id, lap, telemetry_name, telemetry_value, timestamp
        
        Output format (wide):
        vehicle_id, lap, speed, throttle, brake, gear, timestamp
        """
        try:
            # Pivot the data
            pivoted = raw_telemetry.pivot_table(
                index=['vehicle_id', 'lap', 'timestamp'],
                columns='telemetry_name',
                values='telemetry_value',
                aggfunc='first'
            ).reset_index()
            
            print(f"  [INFO] Telemetry pivoted - available columns: {list(pivoted.columns)}")
            return pivoted
        except Exception as e:
            print(f"  [WARN] Error pivoting telemetry: {e}")
            return raw_telemetry
    
    def _get_car_id_column(self):
        """Identify the car ID column name"""
        if self.lap_times is None:
            return None
        
        # Check for common column names
        for col_name in ['CarId', 'vehicle_id', 'Car', 'Vehicle', 'vehicle_number']:
            if col_name in self.lap_times.columns:
                return col_name
        
        # If no match, use the first column
        return self.lap_times.columns[0]
    
    def _get_lap_time_column(self):
        """Identify the lap time column name"""
        if self.lap_times is None:
            return None
        
        # Check for common column names
        for col_name in ['lap_time', 'LapTime', 'laptime', 'time', 'Lap Time', 'elapsed']:
            if col_name in self.lap_times.columns:
                return col_name
        
        return None
    
    def analyze_lap_times(self, car_id=None):
        """Analyze lap time progression and consistency"""
        if self.lap_times is None or self.lap_times.empty:
            return None
        
        df = self.lap_times.copy()
        
        # Get the car ID column name
        car_id_col = self._get_car_id_column()
        
        if car_id and car_id_col:
            df = df[df[car_id_col] == car_id]
        
        if df.empty:
            return None
        
        # Find lap time column
        lap_time_col = self._get_lap_time_column()
        if not lap_time_col:
            return None
        
        analysis = {
            'car_id': car_id,
            'total_laps': len(df),
            'best_lap': df[lap_time_col].min(),
            'worst_lap': df[lap_time_col].max(),
            'avg_lap': df[lap_time_col].mean(),
            'std_dev': df[lap_time_col].std(),
            'consistency_score': 100 - (df[lap_time_col].std() / df[lap_time_col].mean() * 100)
        }
        
        return analysis
    
    def predict_pit_window(self, car_id, current_lap, fuel_per_lap=2.5, tire_deg_rate=3.2):
        """
        Predict optimal pit stop window based on fuel consumption and tire wear
        
        Args:
            car_id: Car identifier
            current_lap: Current lap number
            fuel_per_lap: Fuel consumption per lap (percentage)
            tire_deg_rate: Tire degradation rate per lap (percentage)
        """
        # Simulate current conditions (in real-time, this would come from live telemetry)
        initial_fuel = 100
        initial_tire = 100
        
        # Calculate remaining resources
        fuel_remaining = initial_fuel - (current_lap * fuel_per_lap)
        tire_condition = initial_tire - (current_lap * tire_deg_rate)
        
        # Calculate laps until pit needed
        laps_on_fuel = fuel_remaining / fuel_per_lap
        laps_on_tires = tire_condition / tire_deg_rate
        
        # Determine critical factor
        if laps_on_fuel < laps_on_tires:
            critical_factor = 'fuel'
            laps_remaining = laps_on_fuel
        else:
            critical_factor = 'tires'
            laps_remaining = laps_on_tires
        
        # Optimal window is 2-3 laps before critical
        optimal_pit_lap = current_lap + max(1, int(laps_remaining - 2.5))
        
        recommendation = {
            'car_id': car_id,
            'current_lap': current_lap,
            'fuel_remaining_pct': round(fuel_remaining, 1),
            'tire_condition_pct': round(tire_condition, 1),
            'critical_factor': critical_factor,
            'laps_until_critical': round(laps_remaining, 1),
            'optimal_pit_lap': optimal_pit_lap,
            'pit_window': (optimal_pit_lap - 2, optimal_pit_lap + 2),
            'urgency': 'critical' if laps_remaining < 3 else 'high' if laps_remaining < 6 else 'medium'
        }
        
        return recommendation
    
    def analyze_telemetry_section(self, car_id, section_start, section_end):
        """Analyze telemetry data for a specific track section"""
        if self.telemetry is None:
            return None
        
        df = self.telemetry[self.telemetry['CarId'] == car_id].copy()
        
        # Filter to section
        section_data = df[
            (df['Distance'] >= section_start) & 
            (df['Distance'] <= section_end)
        ]
        
        if len(section_data) == 0:
            return None
        
        analysis = {
            'car_id': car_id,
            'section': f'{section_start}-{section_end}m',
            'avg_speed': section_data['Speed'].mean(),
            'max_speed': section_data['Speed'].max(),
            'min_speed': section_data['Speed'].min(),
            'avg_throttle': section_data['ath'].mean(),
            'braking_points': len(section_data[section_data['pbrake_f'] > 50]),
            'gear_changes': section_data['Gear'].diff().abs().sum()
        }
        
        return analysis
    
    def compare_drivers(self, car_id_1, car_id_2):
        """Compare performance metrics between two drivers"""
        if self.lap_times is None or self.lap_times.empty:
            return None
        
        car_id_col = self._get_car_id_column()
        lap_time_col = self._get_lap_time_column()
        
        if not car_id_col or not lap_time_col:
            return None
        
        car1_data = self.lap_times[self.lap_times[car_id_col] == car_id_1]
        car2_data = self.lap_times[self.lap_times[car_id_col] == car_id_2]
        
        if car1_data.empty or car2_data.empty:
            return None
        
        comparison = {
            'car_1': {
                'id': car_id_1,
                'best_lap': car1_data[lap_time_col].min(),
                'avg_lap': car1_data[lap_time_col].mean(),
                'consistency': car1_data[lap_time_col].std()
            },
            'car_2': {
                'id': car_id_2,
                'best_lap': car2_data[lap_time_col].min(),
                'avg_lap': car2_data[lap_time_col].mean(),
                'consistency': car2_data[lap_time_col].std()
            },
            'delta': {
                'best_lap': car1_data[lap_time_col].min() - car2_data[lap_time_col].min(),
                'avg_lap': car1_data[lap_time_col].mean() - car2_data[lap_time_col].mean(),
                'consistency': car2_data[lap_time_col].std() - car1_data[lap_time_col].std()
            }
        }
        
        return comparison
    
    def generate_race_insights(self, current_lap):
        """Generate strategic insights for race control"""
        insights = []
        
        # Check if lap_times data is available
        if self.lap_times is None or self.lap_times.empty:
            return insights
        
        # Analyze all cars for pit recommendations
        car_id_col = self._get_car_id_column()
        lap_col = self._get_lap_column()
        lap_time_col = self._get_lap_time_column()
        
        if not car_id_col:
            return insights
        
        car_ids = self.lap_times[car_id_col].unique()
        
        for car_id in car_ids[:5]:  # Top 5 cars
            pit_rec = self.predict_pit_window(car_id, current_lap)
            
            if pit_rec['urgency'] == 'critical':
                insights.append({
                    'priority': 'high',
                    'type': 'pit_strategy',
                    'message': f"{car_id}: PIT NOW - {pit_rec['critical_factor']} critical ({pit_rec['laps_until_critical']:.1f} laps remaining)",
                    'car_id': car_id
                })
            elif pit_rec['urgency'] == 'high':
                insights.append({
                    'priority': 'medium',
                    'type': 'pit_strategy',
                    'message': f"{car_id}: Pit window opening in {pit_rec['optimal_pit_lap'] - current_lap} laps",
                    'car_id': car_id
                })
        
        # Analyze lap time trends if lap column exists
        if lap_col and lap_time_col:
            for car_id in car_ids[:3]:
                recent_laps = self.lap_times[
                    (self.lap_times[car_id_col] == car_id) &
                    (self.lap_times[lap_col] >= current_lap - 5) &
                    (self.lap_times[lap_col] <= current_lap)
                ]
                
                if len(recent_laps) >= 3:
                    # Check for degradation
                    lap_times = recent_laps[lap_time_col].values
                    if lap_times[-1] > lap_times[0] + 0.5:
                        insights.append({
                            'priority': 'medium',
                            'type': 'performance',
                            'message': f"{car_id}: Lap times degrading - possible tire wear",
                            'car_id': car_id
                        })
                    elif lap_times[-1] < lap_times[0] - 0.3:
                        insights.append({
                            'priority': 'low',
                            'type': 'performance',
                            'message': f"{car_id}: Improving pace - excellent tire management",
                            'car_id': car_id
                        })
        
        return insights
    
    def export_live_data(self, current_lap, output_file='live_data.json'):
        """Export current race state for dashboard consumption"""
        if self.lap_times is None or self.lap_times.empty:
            return None
        
        car_id_col = self._get_car_id_column()
        lap_time_col = self._get_lap_time_column()
        lap_col = self._get_lap_column()
        
        if not car_id_col or not lap_time_col:
            return None
        
        car_ids = self.lap_times[car_id_col].unique()
        
        race_state = {
            'timestamp': datetime.now().isoformat(),
            'current_lap': current_lap,
            'track': self.track_name,
            'cars': []
        }
        
        for car_id in car_ids:
            car_laps = self.lap_times[self.lap_times[car_id_col] == car_id]
            
            if lap_col:
                current_lap_data = car_laps[car_laps[lap_col] == current_lap]
            else:
                current_lap_data = car_laps.tail(1)
            
            if len(current_lap_data) > 0:
                pit_rec = self.predict_pit_window(car_id, current_lap)
                
                car_data = {
                    'car_id': str(car_id),
                    'position': None,  # Would be calculated from timing
                    'last_lap': float(current_lap_data[lap_time_col].values[0]),
                    'best_lap': float(car_laps[lap_time_col].min()),
                    'avg_lap': float(car_laps[lap_time_col].mean()),
                    'pit_recommendation': pit_rec
                }
                
                race_state['cars'].append(car_data)
        
        # Sort by best lap time (proxy for position)
        race_state['cars'].sort(key=lambda x: x['best_lap'])
        
        # Add positions
        for i, car in enumerate(race_state['cars']):
            car['position'] = i + 1
        
        # Add insights
        race_state['insights'] = self.generate_race_insights(current_lap)
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(race_state, f, indent=2)
        
        return race_state
    
    def _get_lap_column(self):
        """Identify the lap number column name"""
        if self.lap_times is None:
            return None
        
        for col_name in ['Lap', 'lap', 'LapNumber', 'lap_number']:
            if col_name in self.lap_times.columns:
                return col_name
        
        return None


# Example usage and testing
if __name__ == '__main__':
    print("=" * 60)
    print("GR CUP REAL-TIME ANALYTICS ENGINE")
    print("=" * 60)
    print()
    
    # Initialize analytics engine
    analytics = GRCupAnalytics(track_name='barber', race_num=1)
    
    # Load data
    if analytics.load_data():
        print()
        
        # Example: Analyze specific car
        print("📊 CAR ANALYSIS")
        print("-" * 60)
        
        # Get a sample car ID from the data
        sample_car_id = None
        if analytics.lap_times is not None and len(analytics.lap_times) > 0:
            car_id_col = analytics._get_car_id_column()
            if car_id_col:
                sample_car_id = analytics.lap_times[car_id_col].iloc[0]
        
        car_analysis = analytics.analyze_lap_times(car_id=sample_car_id)
        if car_analysis:
            print(f"Car ID: {car_analysis['car_id']}")
            print(f"Best Lap: {car_analysis['best_lap']:.3f}s")
            print(f"Avg Lap: {car_analysis['avg_lap']:.3f}s")
            print(f"Consistency Score: {car_analysis['consistency_score']:.1f}/100")
        else:
            print("No car analysis data available")
        print()
        
        # Example: Pit strategy for current lap
        current_lap = 15
        print(f"🔧 PIT STRATEGY (Lap {current_lap})")
        print("-" * 60)
        pit_rec = analytics.predict_pit_window('CAR_001', current_lap)
        print(f"Fuel Remaining: {pit_rec['fuel_remaining_pct']}%")
        print(f"Tire Condition: {pit_rec['tire_condition_pct']}%")
        print(f"Critical Factor: {pit_rec['critical_factor'].upper()}")
        print(f"Optimal Pit Lap: {pit_rec['optimal_pit_lap']}")
        print(f"Urgency: {pit_rec['urgency'].upper()}")
        print()
        
        # Example: Generate race insights
        print(f"💡 STRATEGIC INSIGHTS (Lap {current_lap})")
        print("-" * 60)
        insights = analytics.generate_race_insights(current_lap)
        for insight in insights[:5]:
            print(f"[{insight['priority'].upper()}] {insight['message']}")
        print()
        
        # Example: Export live data
        print("📤 EXPORTING LIVE DATA")
        print("-" * 60)
        race_state = analytics.export_live_data(current_lap)
        if race_state:
            print(f"Exported data for {len(race_state['cars'])} cars")
            print(f"Generated {len(race_state['insights'])} insights")
            print("Saved to: live_data.json")
        else:
            print("No race state data available")
        print()
        
        print("=" * 60)
        print("[OK] Analytics engine ready for real-time operation")
        print("=" * 60)
