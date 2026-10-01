#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

#define NUM_NODES 5
#define INF 999999
#define MODE_GROUND_TRUCK 0
#define MODE_AIR_RELIEF 1

const char* NODE_NAMES[NUM_NODES] = {
    "Central_Base", "Metro_General", "St_Jude_Clinic", "East_Wing_ER", "South_Relief_Hub"
};

#pragma pack(push, 1)
typedef struct {
    uint8_t magic_byte;      // Protocol Identifier (0xAA)
    uint16_t sender_id;      // Central Base ID (101)
    uint8_t target_node;     // Target Hospital Index (1-4)
    uint8_t dispatch_mode;   // 0 = Ground, 1 = Air
    uint32_t sequence_num;   // Monotonic counter
    uint32_t timestamp;      // Epoch timestamp
    uint8_t payload[64];     // Encrypted Route Payload
    uint8_t hmac_tag[32];    // HMAC Integrity Tag
} TelemetryPacket;
#pragma pack(pop)

void run_dijkstra(int graph[NUM_NODES][NUM_NODES], int src, int dist[NUM_NODES], int parent[NUM_NODES]) {
    int visited[NUM_NODES] = {0};
    for (int i = 0; i < NUM_NODES; i++) {
        dist[i] = INF;
        parent[i] = -1;
    }
    dist[src] = 0;

    for (int count = 0; count < NUM_NODES - 1; count++) {
        int min = INF, u = -1;
        for (int v = 0; v < NUM_NODES; v++) {
            if (!visited[v] && dist[v] <= min) {
                min = dist[v];
                u = v;
            }
        }
        if (u == -1) break;
        visited[u] = 1;

        for (int v = 0; v < NUM_NODES; v++) {
            if (!visited[v] && graph[u][v] && dist[u] != INF && dist[u] + graph[u][v] < dist[v]) {
                dist[v] = dist[u] + graph[u][v];
                parent[v] = u;
            }
        }
    }
}

// Lightweight XOR cipher for Windows GCC simulation without OpenSSL DLLs
void encrypt_payload(const char* input, uint8_t* output_payload, uint8_t* output_hmac) {
    uint8_t key = 0x5A;
    size_t len = strlen(input);
    for (size_t i = 0; i < 64; i++) {
        if (i < len) {
            output_payload[i] = input[i] ^ key;
        } else {
            output_payload[i] = 0x00 ^ key;
        }
    }
    // Generate deterministic 32-byte HMAC simulation tag
    for (int i = 0; i < 32; i++) {
        output_hmac[i] = (uint8_t)((i * 7 + key + len) % 256);
    }
}

int main(int argc, char *argv[]) {
    int target_hospital = 1;
    int road_status = 0;

    if (argc > 1) target_hospital = atoi(argv[1]);
    if (argc > 2) road_status = atoi(argv[2]);

    if (target_hospital < 0 || target_hospital >= NUM_NODES) target_hospital = 1;

    int road_network[NUM_NODES][NUM_NODES] = {
        {0, 12, 25, 18, 30},
        {12, 0, 10, 15, INF},
        {25, 10, 0, 8, 14},
        {18, 15, 8, 0, 12},
        {30, INF, 14, 12, 0}
    };

    int dist[NUM_NODES], parent[NUM_NODES];
    run_dijkstra(road_network, 0, dist, parent);

    uint8_t mode = (road_status == 0) ? MODE_AIR_RELIEF : MODE_GROUND_TRUCK;
    int route_dist = (dist[target_hospital] == INF) ? 15 : dist[target_hospital];

    char raw_msg[64];
    snprintf(raw_msg, sizeof(raw_msg), "DISPATCH|TARGET:%d|MODE:%s|DIST:%dkm",
             target_hospital, (mode == MODE_AIR_RELIEF) ? "AIR" : "GROUND", route_dist);

    TelemetryPacket pkt;
    memset(&pkt, 0, sizeof(TelemetryPacket));
    pkt.magic_byte = 0xAA;
    pkt.sender_id = 101;
    pkt.target_node = (uint8_t)target_hospital;
    pkt.dispatch_mode = mode;
    pkt.sequence_num = 9001;
    pkt.timestamp = (uint32_t)time(NULL);

    encrypt_payload(raw_msg, pkt.payload, pkt.hmac_tag);

    // Save binary struct to data/telemetry_packet.bin
    FILE *f = fopen("../data/telemetry_packet.bin", "wb");
    if (!f) f = fopen("data/telemetry_packet.bin", "wb");

    if (f) {
        fwrite(&pkt, sizeof(TelemetryPacket), 1, f);
        fclose(f);
        printf("[SUCCESS] Telemetry frame compiled & saved to 'data/telemetry_packet.bin'\n");
    } else {
        printf("[ERROR] Could not write telemetry file.\n");
        return 1;
    }
    return 0;
}