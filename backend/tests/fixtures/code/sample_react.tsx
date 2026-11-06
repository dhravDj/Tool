import React from 'react';

export interface ButtonCardProps {
    title: string;
    count: number;
    onClick: () => void;
}

export const ButtonCard: React.FC<ButtonCardProps> = ({ title, count, onClick }) => {
    return (
        <div className="card-box">
            <h4>{title}</h4>
            <p>Score: {count}</p>
            <button onClick={onClick}>Click Me</button>
        </div>
    );
};
