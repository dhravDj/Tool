/**
 * Sample TypeScript module for code intelligence testing.
 */
import { Observable } from 'rxjs';
import axios, { AxiosResponse } from 'axios';

export interface UserProfile {
    id: string;
    email: string;
    roles: string[];
}

export type StatusType = 'active' | 'suspended' | 'pending';

export class AuthenticationManager {
    private secretKey: string = "supersecret";

    public async validateToken(token: string): Promise<boolean> {
        if (!token) {
            return false;
        }
        return token.length > 10;
    }
}

export function formatAddress(city: string, country: string): string {
    return `${city}, ${country}`;
}
