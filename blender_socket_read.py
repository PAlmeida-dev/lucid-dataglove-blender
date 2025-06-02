import bpy
import socket
import threading
import random

# Configuração do socket (conforme o script externo)
HOST = '127.0.0.1'
PORT = 65432

sock = None
running = True
socket_thread = None
arm = None
setup = True
# Dicionário global de valores dos dedos
finger_values = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0}

# Nome do objeto Armature e dos ossos
# === Configuração geral ===
ARMATURE_NAME = "Armature"

CONTROL_BONE_MAPPING = {
    'A': 'thumb.03.L_end',
    'B': 'finger_index.03.L_end',
    'C': 'finger_middle.03.L_end',
    'D': 'finger_ring.03.L_end',
    'E': 'finger_pinky.03.L_end',
}

BONE_MAPPING = {
    'A': 'thumb.03.L',
    'B': 'finger_index.03.L',
    'C': 'finger_middle.03.L',
    'D': 'finger_ring.03.L',
    'E': 'finger_pinky.03.L',
}

CURVE_MAPPING = {
    'A': 'thumb_path',
    'B': 'index_path',
    'C': 'middle_path',
    'D': 'ring_path',
    'E': 'pinky_path',
}

PROP_MAPPING = {
    'A': 'thumb_control',
    'B': 'index_control',
    'C': 'middle_control',
    'D': 'ring_control',
    'E': 'pinky_control',
}

def lucid_dataglove_handling(data):
    global finger_values
    try:
        decoded = data.decode('utf-8')
        parts = decoded.split(',')
        for part in parts:
            label, value = part.split(':')
            finger_values[label] = min(1.0,(int(value) / 4095.0))
    except Exception as e:
        print(f"Erro no socket: {e}")

# Handler que atualiza os ossos
def update_bones():
    global arm, finger_values
    for label in finger_values:
        arm[PROP_MAPPING[label]] = finger_values[label]
    arm.animation_data.drivers.update()
    return

def start_sock_thread():
    global sock, running

    def execute():
        global sock,running
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind((HOST, PORT))
            sock.settimeout(1.0)
            print(f"Escutando em {HOST}:{PORT}")
            print("Esperando dados da luva...")
            while running:
                try:
                    data, addr = sock.recvfrom(1024)
                    print(f"dados recebidos{data}")
                    bpy.app.timers.register(lambda data=data: lucid_dataglove_handling(data))
                    update_bones()
                except socket.timeout:
                    continue
                except BlockingIOError:
                    pass  # sem novos dados
                except Exception as e:
                    if running:
                        print(f"Erro ao receber dados: {e}")
        except Exception as e:
            print(f"Conexão socket falhou em {HOST}:{PORT}. Error: {e}")
            print("Outra conexão pode estar usando a porta")
        finally:
            if sock:
                sock.close()
                print("Socket Fechado")
    thread = threading.Thread(target=execute, daemon=True)
    thread.start()
    self.report({'INFO'}, "Leitura UDP iniciada")
    return thread

def end_sock_thread():
    global running, sock, socket_thread
    running = False
    if sock:
        sock.close()
    if socket_thread:
        socket_thread.join(2.0)  # Wait for thread to finish, but not forever
    print("Conexão interrompida")



def setup_armature():
    armature = bpy.data.objects.get(ARMATURE_NAME)
    if not armature or armature.type != 'ARMATURE':
        raise ValueError(f"Objeto '{ARMATURE_NAME}' não encontrado ou não é um Armature.")
    return armature

def setup_IK():
    global arm
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode='POSE')
    for label in BONE_MAPPING:
        target_bone_name = CONTROL_BONE_MAPPING[label]
        bone_name = BONE_MAPPING[label]
        
        try:
            pbone = arm.pose.bones[bone_name]
            ik = pbone.constraints.new(type='IK')
            ik.target = arm
            ik.subtarget = target_bone_name
            ik.chain_count = 2 if bone_name.startswith("thumb") else 3
            print(f"IK adicionado em {bone_name} → {target_bone_name}")
        except KeyError:
            print(f"Osso '{bone_name}' ou controlador '{target_bone_name}' não encontrado.")
        except Exception as e:
            print(f"Erro ao adicionar IK para {bone_name}: {e}")

# === Setup Follow Path com Empty intermediário ===
def setup_follow_path_with_empty(label):
    global arm
    curve_name = CURVE_MAPPING[label]
    prop_name = PROP_MAPPING[label]
    display_name = prop_name.split("_")[0]
    ctrl_bone_name = CONTROL_BONE_MAPPING[label]

    curve_obj = bpy.data.objects.get(curve_name)
    if not curve_obj:
        print(f"Curva '{curve_name}' não encontrada.")
        return

    # Cria propriedade customizada
    if prop_name not in arm:
        arm[prop_name] = 0.0
    if not hasattr(bpy.types.Object, prop_name):
        setattr(bpy.types.Object, prop_name, bpy.props.FloatProperty(
            name=display_name,
            description=f"Controle do dedo {display_name}",
            min=0.0,
            max=1.0,
            default=0.0
        ))

    # Recupera osso de controle
    pbone = arm.pose.bones.get(ctrl_bone_name)
    if not pbone:
        print(f"Osso de controle '{ctrl_bone_name}' não encontrado.")
        return

    # Cria um Empty auxiliar
    empty_name = f"Follow_{label}_Empty"
    if empty_name in bpy.data.objects:
        empty = bpy.data.objects[empty_name]
    else:
        empty = bpy.data.objects.new(empty_name, None)
        bpy.context.collection.objects.link(empty)
        empty.empty_display_type = 'SPHERE'

    # Constraint Follow Path no Empty
    follow = empty.constraints.get("Follow Path")
    if not follow:
        follow = empty.constraints.new(type='FOLLOW_PATH')
    follow.target = curve_obj
    follow.use_curve_follow = True
    follow.use_fixed_location = True
    follow.offset_factor = 0.0

    # Driver no offset_factor
    fcurve = follow.driver_add("offset_factor")
    driver = fcurve.driver
    driver.type = 'SCRIPTED'
    var = driver.variables.new()
    var.name = label
    var.type = 'SINGLE_PROP'
    var.targets[0].id = arm
    var.targets[0].data_path = f'["{prop_name}"]'
    driver.expression = label

    # Bone segue o Empty via Copy Transforms
    copy = pbone.constraints.get("Copy Transforms")
    if not copy:
        copy = pbone.constraints.new(type='COPY_TRANSFORMS')
    copy.target = empty

if __name__ == "__main__":
    try:
        arm = setup_armature()
        if not setup:
            setup_IK()
            for label in CONTROL_BONE_MAPPING:
                setup_follow_path_with_empty(label)
            setup = True
        socket_thread = start_sock_thread()
    except Exception as e:
        print(f"Erro ao inicializar o listener: {e}")
