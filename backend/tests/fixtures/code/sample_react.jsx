import React, { useState } from 'react';

export function CounterWidget({ initialCount = 0 }) {
    const [count, setCount] = useState(initialCount);

    const handleIncrement = () => {
        setCount(c => c + 1);
    };

    return (
        <div className="counter-container">
            <h3>Current Count: {count}</h3>
            <button onClick={handleIncrement}>Increment</button>
        </div>
    );
}

export default CounterWidget;
