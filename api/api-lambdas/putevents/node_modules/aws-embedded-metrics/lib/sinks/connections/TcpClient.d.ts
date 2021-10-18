/// <reference types="node" />
import { IEndpoint } from './IEndpoint';
import { ISocketClient } from './ISocketClient';
export declare class TcpClient implements ISocketClient {
    private endpoint;
    private socket;
    constructor(endpoint: IEndpoint);
    warmup(): Promise<void>;
    sendMessage(message: Buffer): Promise<void>;
    private disconnect;
    private waitForOpenConnection;
    private establishConnection;
}
