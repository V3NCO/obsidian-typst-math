import { expect, test } from "vitest";
import { response_verifier, server } from "../setup";
import { LmatEnvironment } from "../../models/cas/LmatEnvironment";
import { TruthTableArgsPayload, TruthTableFormat, TruthTableMessage, TruthTableResponse } from "../../models/cas/messages/TruthTableMessage";

test('Test TruthTable Message (markdown)', async () => {
    const response = response_verifier.verifyResponse<TruthTableResponse>(await server.send(
        new TruthTableMessage(new TruthTableArgsPayload("p \\wedge q", new LmatEnvironment(), TruthTableFormat.MARKDOWN))
    ).response);

    const md = response.truth_table;

    expect(md).toContain('|');
    expect(md.split('\n')[0]).toContain("$p$");
    expect(md.split('\n')[0]).toContain("$q$");
});

test('Test TruthTable Message (typst table)', async () => {
    const response = response_verifier.verifyResponse<TruthTableResponse>(await server.send(
        new TruthTableMessage(new TruthTableArgsPayload("p \\vee q", new LmatEnvironment(), TruthTableFormat.TYPST_TABLE))
    ).response);

    const typst = response.truth_table;
    expect(typst).toContain("#table(");
    expect(typst).toContain("columns:");
    expect(typst).toContain("p");
    expect(typst).toContain("q");
});
