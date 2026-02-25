import { GenericPayload, StartCommandMessage } from "../../../services/CasServer";
import { LmatEnvironment } from "../LmatEnvironment";

// Enum of all possible truth table formats returned by the cas client
export enum TruthTableFormat {
    // truth table contents is formatted as a markdown table with typst entries.
    MARKDOWN = "md",
    // truth table is formatted as a Typst #table(), renderable by the typst plugin
    TYPST_TABLE = "typst-table",
}

export class TruthTableArgsPayload implements GenericPayload {
    public constructor(
        public expression: string,
        public environment: LmatEnvironment,
        public truth_table_format: TruthTableFormat
    ) { }
    [x: string]: unknown;
}

export class TruthTableMessage extends StartCommandMessage {
    public constructor(args: TruthTableArgsPayload) {
        super({ command_type: 'truth-table', start_args: args });
    }
}

export interface TruthTableResponse {
    truth_table: string
}

