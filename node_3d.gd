extends CharacterBody3D
# Godot 4.x. Повесьте на CharacterBody3D, внутри которого лежит ваша фигурка.

const SPEED = 5.0
const JUMP_VELOCITY = 4.5

var gravity = ProjectSettings.get_setting("physics/3d/default_gravity")
var anim: AnimationPlayer


func _ready():
	# Ищем AnimationPlayer среди дочерних узлов (если он есть)
	anim = find_child("AnimationPlayer", true, false)
	if anim:
		print("Анимации: ", anim.get_animation_list())


func _physics_process(delta):
	# Гравитация
	if not is_on_floor():
		velocity.y -= gravity * delta

	# Прыжок на пробел
	if Input.is_key_pressed(KEY_SPACE) and is_on_floor():
		velocity.y = JUMP_VELOCITY

	# Ходьба на WASD или стрелки
	var x = Input.get_axis("ui_left", "ui_right")
	var z = Input.get_axis("ui_up", "ui_down")
	if Input.is_key_pressed(KEY_A): x = -1
	if Input.is_key_pressed(KEY_D): x = 1
	if Input.is_key_pressed(KEY_W): z = -1
	if Input.is_key_pressed(KEY_S): z = 1

	var direction = Vector3(x, 0, z).normalized()

	if direction != Vector3.ZERO:
		velocity.x = direction.x * SPEED
		velocity.z = direction.z * SPEED
		# Поворачиваем фигурку лицом по направлению движения
		rotation.y = lerp_angle(rotation.y, atan2(direction.x, direction.z), 10 * delta)
	else:
		velocity.x = move_toward(velocity.x, 0, SPEED)
		velocity.z = move_toward(velocity.z, 0, SPEED)

	move_and_slide()

	# Анимация (если есть). Впишите свои названия.
	if anim:
		var name = "walk" if direction != Vector3.ZERO else "idle"
		if anim.has_animation(name) and anim.current_animation != name:
			anim.play(name)
