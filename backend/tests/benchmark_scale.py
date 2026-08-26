import time
import numpy as np
from app.simulation.physics_engine import MachinePhysicsState
from app.ml.feature_extractor import extract_features_from_window
from app.ml.inference import predict_machine_health

def run_scale_benchmark():
    print("================================================================")
    print(" FACTORYIQ LOAD & SCALE SANITY BENCHMARK")
    print("================================================================")
    
    scale_levels = [24, 100, 200, 500]
    
    for num_machines in scale_levels:
        # Create virtual machines
        machines = [
            MachinePhysicsState(
                machine_id=i + 1,
                name=f"BENCH-MCH-{i:03d}",
                machine_type="5-Axis Mill" if i % 2 == 0 else "CNC Lathe",
                zone="Cell B"
            )
            for i in range(num_machines)
        ]
        
        # 1. Measure 10-step physics simulation tick time
        t0 = time.perf_counter()
        windows = {m.machine_id: [] for m in machines}
        for _ in range(10):
            for m in machines:
                windows[m.machine_id].append(m.tick())
        t_sim = time.perf_counter() - t0
        
        # 2. Measure feature extraction time across all machines
        t0 = time.perf_counter()
        feature_matrices = [extract_features_from_window(windows[m.machine_id]) for m in machines]
        t_feat = time.perf_counter() - t0
        
        # 3. Measure full multi-model AI inference time across all machines
        t0 = time.perf_counter()
        inferences = [predict_machine_health(windows[m.machine_id], criticality="High") for m in machines]
        t_infer = time.perf_counter() - t0
        
        total_time = t_sim + t_feat + t_infer
        throughput_hz = num_machines / total_time
        avg_infer_latency_ms = (t_infer / num_machines) * 1000.0
        
        print(f"[{num_machines:3d} Machines] Total Cycle: {total_time * 1000.0:6.1f}ms | "
              f"Sim: {t_sim*1000:5.1f}ms | Feat: {t_feat*1000:5.1f}ms | "
              f"AI Inference: {t_infer*1000:5.1f}ms ({avg_infer_latency_ms:4.2f}ms/asset) | "
              f"Throughput: {throughput_hz:6.1f} updates/sec")

if __name__ == "__main__":
    run_scale_benchmark()
