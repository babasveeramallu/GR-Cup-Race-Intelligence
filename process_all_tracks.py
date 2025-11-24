import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from Stragery_engine import GRCupAnalytics


def verify_data_integrity(race_data):
    """
    Verify that lap times are valid and not from the old 0.001s bug
    
    Returns: (is_valid, issues_found)
    """
    issues = []
    
    if not race_data or not isinstance(race_data, dict):
        return False, ["Invalid race data structure"]
    
    # Check if we have cars
    cars = race_data.get('cars', [])
    if not cars:
        return False, ["No cars found in race data"]
    
    # Check for the old 0.001s bug
    bad_lap_times = []
    for car in cars:
        best_lap = car.get('best_lap_time', 0)
        if best_lap < 10:  # Any lap under 10s is unrealistic for racing
            bad_lap_times.append({
                'car': car.get('car_id', 'Unknown'),
                'lap_time': best_lap
            })
    
    if bad_lap_times:
        count = len(bad_lap_times)
        issues.append(f"[CRITICAL] Found {count} cars with lap times < 10s (possible 0.001s bug)")
        for item in bad_lap_times[:3]:  # Show first 3
            issues.append(f"  - Car {item['car']}: {item['lap_time']}s")
        return False, issues
    
    return True, []


def process_single_race(track_name, race_num, track_path):
    """
    Process a single race and return comprehensive analysis
    """
    try:
        # Initialize analytics engine
        analytics = GRCupAnalytics(track_name=track_name, race_num=race_num)
        analytics.data_dir = Path(track_path)
        
        # Load data
        if not analytics.load_data():
            print(f"  [FAIL] Failed to load data for {track_name.upper()} Race {race_num}")
            return None
        
        # Get basic statistics
        if analytics.lap_times is None or analytics.lap_times.empty:
            print(f"  [WARN] No lap data for {track_name.upper()} Race {race_num}")
            return None
        
        car_id_col = analytics._get_car_id_column()
        lap_time_col = analytics._get_lap_time_column()
        lap_col = analytics._get_lap_column()
        
        if not car_id_col or not lap_time_col:
            return None
        
        # Get current lap (use the max lap number)
        current_lap = int(analytics.lap_times[lap_col].max()) if lap_col else 50
        
        # Build race summary
        race_data = {
            'track': track_name.upper(),
            'race': race_num,
            'timestamp': datetime.now().isoformat(),
            'current_lap': current_lap,
            'total_laps_completed': current_lap,
            'cars': [],
            'insights': [],
            'weather': None,
            'top_performers': []
        }
        
        # Get weather data if available
        if analytics.weather is not None and len(analytics.weather) > 0:
            try:
                weather_row = analytics.weather.iloc[0]
                # Handle different weather data formats
                temp = None
                try:
                    temp = float(str(weather_row.iloc[0]).split(';')[2]) if pd.notna(weather_row.iloc[0]) else None
                except Exception:
                    temp = None
                
                race_data['weather'] = {
                    'temperature': temp,
                    'conditions': 'Mixed'
                }
            except Exception:
                race_data['weather'] = {'temperature': None, 'conditions': 'Unknown'}
        
        # Analyze all cars
        car_ids = analytics.lap_times[car_id_col].unique()
        
        for car_id in car_ids:
            car_laps = analytics.lap_times[analytics.lap_times[car_id_col] == car_id]
            
            if len(car_laps) > 0:
                best_lap = float(car_laps[lap_time_col].min())
                avg_lap = float(car_laps[lap_time_col].mean())
                
                car_data = {
                    'car_id': str(car_id),
                    'total_laps': len(car_laps),
                    'best_lap_time': round(best_lap, 3),
                    'avg_lap_time': round(avg_lap, 3),
                    'consistency_score': round(100 - (car_laps[lap_time_col].std() / avg_lap * 100), 1),
                    'pit_recommendation': analytics.predict_pit_window(car_id, current_lap),
                    'status': 'Active'
                }
                
                race_data['cars'].append(car_data)
        
        # Sort cars by best lap
        race_data['cars'].sort(key=lambda x: x['best_lap_time'])
        
        # Add positions
        for idx, car in enumerate(race_data['cars']):
            car['position'] = idx + 1
            if idx < 5:
                race_data['top_performers'].append({
                    'position': idx + 1,
                    'car_id': car['car_id'],
                    'best_lap': car['best_lap_time']
                })
        
        # Generate insights
        race_data['insights'] = analytics.generate_race_insights(current_lap)
        
        # Verify data integrity (check for 0.001s bug)
        is_valid, issues = verify_data_integrity(race_data)
        if not is_valid:
            print(f"  [WARN] Data integrity issues in {track_name.upper()} Race {race_num}:")
            for issue in issues:
                print(f"         {issue}")
        
        print(f"  [OK] {track_name.upper()} Race {race_num}: {len(race_data['cars'])} cars, {len(race_data['insights'])} insights")
        
        return race_data
        
    except Exception as e:
        print(f"  [FAIL] Error processing {track_name.upper()} Race {race_num}: {e}")
        import traceback
        traceback.print_exc()
        return None


def process_all_tracks():
    """
    Process all race tracks and generate comprehensive race intelligence
    """
    
    base_path = Path('.')
    tracks = ['barber', 'COTA', 'indianapolis', 'Road America', 'sebring', 'Sonoma', 'VIR']
    
    all_results = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_tracks': 0,
            'successful_tracks': 0,
            'total_races': 0,
            'total_cars': 0,
            'total_insights': 0
        },
        'tracks': []
    }
    
    print("=" * 80)
    print("MULTI-TRACK RACE INTELLIGENCE REPORT")
    print("=" * 80)
    print()
    
    for track_name in tracks:
        track_path = base_path / track_name
        
        # Handle COTA and Road America which have Race 1/Race 2 subdirectories
        if track_path.exists() and (track_path / 'Race 1').exists():
            print(f">>> Processing {track_name.upper()} (Multi-Race Structure)")
            print("-" * 80)
            
            for race_num in [1, 2]:
                race_dir = track_path / f'Race {race_num}'
                if race_dir.exists():
                    result = process_single_race(track_name.lower(), race_num, race_dir)
                    if result:
                        all_results['tracks'].append(result)
                        all_results['summary']['total_races'] += 1
                        all_results['summary']['total_cars'] += len(result.get('cars', []))
                        all_results['summary']['total_insights'] += len(result.get('insights', []))
                        print()
        
        elif track_path.exists():
            print(f">>> Processing {track_name.upper()}")
            print("-" * 80)
            
            for race_num in [1, 2]:
                result = process_single_race(track_name.lower(), race_num, track_path)
                if result:
                    all_results['tracks'].append(result)
                    all_results['summary']['total_races'] += 1
                    all_results['summary']['total_cars'] += len(result.get('cars', []))
                    all_results['summary']['total_insights'] += len(result.get('insights', []))
                    print()
    
    all_results['summary']['total_tracks'] = len(tracks)
    all_results['summary']['successful_tracks'] = len([t for t in all_results['tracks'] if t is not None]) // 2
    
    # Save consolidated results
    output_file = 'all_tracks_results.json'
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    # Final verification - check all races for data integrity
    print("\n" + "=" * 80)
    print("FINAL DATA VERIFICATION")
    print("=" * 80)
    all_valid = True
    for track_data in all_results['tracks']:
        if track_data:
            is_valid, issues = verify_data_integrity(track_data)
            if not is_valid:
                all_valid = False
                print(f"[CRITICAL] {track_data['track']} Race {track_data['race']} failed verification!")
                for issue in issues:
                    print(f"  {issue}")
            else:
                lap_count = len(track_data.get('cars', []))
                best_lap = min([c.get('best_lap_time', 999) for c in track_data.get('cars', [])]) if lap_count > 0 else 0
                print(f"[OK] {track_data['track']} Race {track_data['race']}: {lap_count} cars, best lap {best_lap:.2f}s")
    
    if all_valid:
        print("\n[OK] All data passed integrity checks!")
    else:
        print("\n[WARN] Some data failed integrity checks. Please review above.")
    print("=" * 80)
    
    print("\n" + "=" * 80)
    print("SUMMARY REPORT")
    print("=" * 80)
    print(f"Total Tracks Processed: {all_results['summary']['total_tracks']}")
    print(f"Total Races Analyzed: {all_results['summary']['total_races']}")
    print(f"Total Cars: {all_results['summary']['total_cars']}")
    print(f"Total Strategic Insights: {all_results['summary']['total_insights']}")
    print(f"\n[OK] Results saved to: {output_file}")
    print("=" * 80)
    
    return all_results


def generate_html_report(all_results):
    """
    Generate an HTML dashboard from the results
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>GR Cup Race Intelligence Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .header { background-color: #1a1a1a; color: #fff; padding: 20px; border-radius: 5px; }
            .summary { background-color: #fff; padding: 15px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .track-section { background-color: #fff; padding: 20px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .track-title { color: #d32f2f; font-size: 24px; margin-bottom: 15px; }
            table { width: 100%; border-collapse: collapse; margin: 15px 0; }
            th { background-color: #f5f5f5; padding: 10px; text-align: left; border-bottom: 2px solid #ddd; }
            td { padding: 10px; border-bottom: 1px solid #eee; }
            tr:hover { background-color: #f9f9f9; }
            .top-performer { color: #2e7d32; font-weight: bold; }
            .insight { background-color: #e3f2fd; padding: 10px; margin: 5px 0; border-left: 4px solid #1976d2; border-radius: 3px; }
            .metric { display: inline-block; margin: 10px 20px 10px 0; }
            .metric-label { font-weight: bold; color: #666; }
            .metric-value { font-size: 24px; color: #d32f2f; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏁 GR Cup Multi-Track Race Intelligence Report</h1>
            <p>Generated: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
        </div>
        
        <div class="summary">
            <h2>Executive Summary</h2>
            <div class="metric">
                <div class="metric-label">Total Tracks</div>
                <div class="metric-value">""" + str(all_results['summary']['total_tracks']) + """</div>
            </div>
            <div class="metric">
                <div class="metric-label">Races Analyzed</div>
                <div class="metric-value">""" + str(all_results['summary']['total_races']) + """</div>
            </div>
            <div class="metric">
                <div class="metric-label">Total Cars</div>
                <div class="metric-value">""" + str(all_results['summary']['total_cars']) + """</div>
            </div>
            <div class="metric">
                <div class="metric-label">Strategic Insights</div>
                <div class="metric-value">""" + str(all_results['summary']['total_insights']) + """</div>
            </div>
        </div>
    """
    
    # Add track details
    for track_data in all_results.get('tracks', []):
        html_content += f"""
        <div class="track-section">
            <div class="track-title">{track_data['track']} - Race {track_data['race']}</div>
            
            <h3>Race Status</h3>
            <div class="metric">
                <div class="metric-label">Current Lap</div>
                <div class="metric-value">{track_data['current_lap']}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Drivers</div>
                <div class="metric-value">{len(track_data['cars'])}</div>
            </div>
            
            <h3>Top Performers</h3>
            <table>
                <tr>
                    <th>Position</th>
                    <th>Car ID</th>
                    <th>Best Lap Time</th>
                </tr>
        """
        
        for perf in track_data.get('top_performers', [])[:5]:
            html_content += f"""
                <tr>
                    <td class="top-performer">{perf['position']}</td>
                    <td>{perf['car_id']}</td>
                    <td>{perf['best_lap']:.3f}s</td>
                </tr>
            """
        
        html_content += """
            </table>
            
            <h3>Race Intelligence</h3>
        """
        
        for insight in track_data.get('insights', [])[:5]:
            priority = insight.get('priority', 'info').upper()
            message = insight.get('message', 'No message')
            html_content += f"""
            <div class="insight">
                <strong>[{priority}]</strong> {message}
            </div>
            """
        
        html_content += """
        </div>
        """
    
    html_content += """
    </body>
    </html>
    """
    
    with open('race_report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("[OK] HTML report generated: race_report.html")


if __name__ == '__main__':
    # Process all tracks
    all_results = process_all_tracks()
    
    # Generate HTML report
    print("\nGenerating HTML report...")
    generate_html_report(all_results)
    
    print("\n" + "=" * 80)
    print("[OK] Processing complete! Check:")
    print("  - all_tracks_results.json (detailed data)")
    print("  - race_report.html (visual dashboard)")
    print("=" * 80)
