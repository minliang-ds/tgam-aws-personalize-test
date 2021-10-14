/**
 * Fetch JSON data from an remote HTTP endpoint and de-serialize to the provided type.
 * There are no guarantees the response will conform to the contract defined by T.
 * It is up to the consumer to ensure the provided T captures all possible response types
 * from the provided endpoint.
 *
 * @param url - currently only supports HTTP
 */
declare const fetch: <T>(url: string) => Promise<T>;
export { fetch };
