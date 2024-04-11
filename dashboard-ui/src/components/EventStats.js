import React, { useEffect, useState } from 'react';
import '../App.css';

export default function EventStats() {
    const [isLoaded, setIsLoaded] = useState(false);
    const [stats, setStats] = useState({});
    const [error, setError] = useState(null);

    const getEventStats = () => {
        fetch(`http://kafka3855.westus3.cloudapp.azure.com:8120/event_stats`) 
            .then(res => res.json())
            .then(
                (result) => {
                    console.log("Received Event Log stats", result);
                    setStats(result);
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
                <h1>Event Log Statistics</h1>
                <div>0001 Events: {stats['0001']}</div>
                <div>0002 Events: {stats['0002']}</div>
                <div>0003 Events: {stats['0003']}</div>
                <div>0004 Events: {stats['0004']}</div>
            </div>
        );
    }
}