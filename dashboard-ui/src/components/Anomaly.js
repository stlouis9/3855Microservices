import React, { useEffect, useState } from 'react';
import '../App.css';

export default function Anomaly() {
    const [isLoaded, setIsLoaded] = useState(false);
    const [movieStats, setMovieStats] = useState({});
    const [reviewStats, setReviewStats] = useState({});
    const [error, setError] = useState(null);

    const getEventStats = () => {
        fetch(`http://kafka3855.westus3.cloudapp.azure.com/anomaly_detector/anomaly_stats?anomaly_type=tooHigh`) 
            .then(res => res.json())
            .then(
                (result) => {
                    console.log("Received movie anomalies", result);
                    setMovieStats(result);
                    setIsLoaded(true);
                },
                (error) => {
                    setError(error);
                    setIsLoaded(true);
                }
            );
        fetch(`http://kafka3855.westus3.cloudapp.azure.com/anomaly_detector/anomaly_stats?anomaly_type=tooLow`) 
            .then(res => res.json())
            .then(
                (result) => {
                    console.log("Received review anomalies", result);
                    setReviewStats(result);
                    setIsLoaded(true);
                },
                (error) => {
                    setError(error);
                    setIsLoaded(true);
                }
            );
    };

    useEffect(() => {
        const interval = setInterval(getEventStats, 2000);
        return () => clearInterval(interval);
    }, []);

    if (error) {
        return <div className="error">Error: {error.message}</div>;
    } else if (!isLoaded) {
        return <div>Loading...</div>;
    } else {
        return (
            <div>
                <h1>Anomaly Log</h1>
                <div>Movie Anomalies: {movieStats['num_anomalies']}</div>
                <div>{movieStats['most_recent_desc']}</div>
                <div>Detected on {movieStats['most_recent_datetime']}</div>

                <div>Review Anomalies: {reviewStats['num_anomalies']}</div>
                <div>{reviewStats['most_recent_desc']}</div>
                <div>Detected on {reviewStats['most_recent_datetime']}</div>
            </div>
        );
    }
}